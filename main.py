import logging
import time
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import joblib
import numpy as np
import pandas as pd


# Genero un tipo de error propio para errores de validacion
class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)


# Creo una interfaz para validar datos en predict
class ModelWrapper:
    def __init__(self, model, vals={}):
        self.model = model
        self.vals = vals

    def validate(self, df):
        for col, val_rules in self.vals.items():

            val_type, pos_values, nullable = val_rules

            null_cond = df[col].isna().any() if not nullable else False

            if val_type == 'range':
                s, e = pos_values
                if not (((df[col] >= s) & (df[col] <= e)) | df[col].isna()).all() or null_cond:
                    logging.error(f'ValidationError found for col {col}')
                    raise ValidationError(f'Invalid range for {col}')

            if val_type == 'categorical':
                if not df[col].isin(pos_values).all() or null_cond:
                    logging.error(f'ValidationError found for col {col}')
                    raise ValidationError(f'Invalid value for {col}')
        return True

    def predict(self, df):
        try:
            self.validate(df)
            logging.info('Batch ready for prediction')
            return self.model.predict(df)
        except ValidationError as e:
            raise e


class Policy(BaseModel):
    CUSTOMER_SENIORITY: int
    SEX: int
    INSR_TYPE: int
    INSURED_VALUE: float
    PREMIUM: float
    PROD_YEAR: float
    SEATS_NUM: float
    CARRYING_CAPACITY: float
    CCM_TON: float
    MONTH_BEGIN: int
    MONTH_END: int
    YEAR_BEGIN: int
    YEAR_END: int


models = {}

logger = logging.getLogger(__name__)


# Precargo en memoria el modelo para no levantarlo por consulta
# En base a la exploracion en exp.ipynb, genero reglas de data quality para rechazar registros no validos
# Podrian generarse de forma dinamica del DF, tomando si es categorica o no, los valores posibles y la cantidad de registros contra el total, pero por simplicidad y procesamiento se decidio usar esta solucion
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Columna: (Tipo de validacion, rango/valores validos, Si es nulleable)
    val_dict = {'CUSTOMER_SENIORITY': ('range', (0, np.inf), False),
                'SEX': ('categorical', [0, 1], False),
                'INSR_TYPE': ('categorical', [1201, 1202, 1204], False),
                'INSURED_VALUE': ('range', (0, np.inf), False),
                'PREMIUM': ('range', (0, np.inf), True),
                'PROD_YEAR': ('range', (1950, np.inf), False),
                'SEATS_NUM': ('range', (0, np.inf), True),
                'CARRYING_CAPACITY': ('range', (0, np.inf), True),
                'CCM_TON': ('range', (0, np.inf), False),
                'MONTH_BEGIN': ('range', (1, 12), False),
                'MONTH_END': ('range', (1, 12), False),
                'YEAR_BEGIN': ('range', (2014, datetime.today().year), False),
                'YEAR_END': ('range', (2014, datetime.today().year), False)}
    logger.info('Loading model...')
    models['lc'] = ModelWrapper(joblib.load('model.pkl'), val_dict)
    logger.info('Model loaded.')

    yield

    models.clear()

app = FastAPI(lifespan=lifespan)


# Endpoints son identicos, unicamente cambia la cantidad recibida. Se unifica logica en una sola funcion
def pred_routine(df):
    s = time.time()
    df = df.replace(-999, np.nan)
    predictions = models['lc'].predict(df)
    ms = (time.time() - s) * 1000
    return {'predictions': predictions.tolist(),
            'ms': ms,
            'timestamp': datetime.now()}


@app.post('/predict_item')
async def predict_item(item: Policy):
    logger.info('Item received for prediction.')
    return pred_routine(pd.DataFrame([item.model_dump()]))


@app.post('/predict_batch')
async def predict_batch(items: List[Policy]):
    logger.info('Batch received for prediction.')
    return pred_routine(pd.DataFrame(item.model_dump() for item in items))

# Defino workers adicionales para poder gestionar el flujo de streaming y batch simultaneamente
# Idealmente, tendria un hilo dedicado al endpoint de streaming o que funcione con un source y sink
if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, workers=4)
