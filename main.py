from datetime import datetime
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import joblib
import numpy as np
import pandas as pd

class Item(BaseModel):
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

class ValidationError(Exception):
    pass

# Creo una interfaz para validar datos en predict
class ModelWrapper:
    def __init__(self, model, vals=None):
        self.model = model 
        self.vals = vals

    def predict(self, df):
        for col, val_rules in self.vals.items():
            try:
                values = df[col] 
            except:
                raise ValidationError(f'No fue provisto el valor para {col}')
            
            val_type, pos_values = val_rules

            if val_type == 'range':
                s, e = pos_values
                if not ((values >= s) & (values <= e)).all():
                    raise ValidationError(f'Variable {col} no se encuentra en un rango valido')
                
            if val_type == 'categorical':
                if not values.isin(pos_values).all():
                    raise ValidationError(f'Variable {col} no se encuentra entre las categorias validas')

        return self.model.predict(df)

models = {}

# Precargo en memoria el modelo para no levantarlo por consulta
# En base a la exploracion en exp.ipynb, genero reglas de data quality para rechazar registros no validos
# Podrian generarse de forma dinamica del DF (e info adicional), pero en este primer MVP las defino de forma manual en un diccionario con tuplas con el tipo de constraint y los valores posibles
@asynccontextmanager
async def lifespan(app: FastAPI):
    val_dict = {'CUSTOMER_SENIORITY':('range', (0, np.inf)), 
                'SEX':('categorical', [0, 1]),
                'INSR_TYPE':('categorical', [1201, 1202, 1204]), 
                'INSURED_VALUE':('range', (0, np.inf)), 
                'PREMIUM':('range', (0, np.inf)), 
                'PROD_YEAR':('range', (1950, np.inf)), 
                'SEATS_NUM':('range', (0, np.inf)), 
                'CARRYING_CAPACITY':('range', (0, np.inf)), 
                'CCM_TON':('range', (0, np.inf)), 
                'MONTH_BEGIN':('range', (1, 12)), 
                'MONTH_END':('range', (1, 12)), 
                'YEAR_BEGIN':('range', (2014, datetime.today().year)), 
                'YEAR_END':('range', (2014, datetime.today().year))}
    models['lc'] = ModelWrapper(joblib.load('model.pkl'), val_dict)

    yield

    models.clear()
    
app = FastAPI(lifespan=lifespan)

@app.post('/predict_item')
def predict_item(item: Item):
    predictions = models['lc'].predict(pd.DataFrame([item.model_dump()]))
    return {'prediction':predictions.tolist()[0]}

@app.post('/predict_batch')
def predict_batch(items: List[Item]):
    predictions = models['lc'].predict(pd.DataFrame(item.model_dump() for item in items))
    return {'predictions':predictions.tolist()}

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)