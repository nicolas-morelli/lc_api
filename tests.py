import os
import requests
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Defino el preprocesamiento necesario para utilizar el modelo. De acuerdo a exp.ipynb
def preprocess_df(df):
    vdir = os.path.dirname(os.path.abspath(__file__))
    vpath = os.path.join(vdir, 'vehicle_info.csv')
    veh = pd.read_csv(vpath)
    df['INSR_BEGIN'] = pd.to_datetime(df['INSR_BEGIN'], format='%d-%b-%y')
    df['INSR_END'] = pd.to_datetime(df['INSR_BEGIN'], format='%d-%b-%y')
    df['MONTH_BEGIN'] = df['INSR_BEGIN'].dt.month
    df['MONTH_END'] = df['INSR_END'].dt.month
    df['YEAR_BEGIN'] = df['INSR_BEGIN'].dt.year
    df['YEAR_END'] = df['INSR_END'].dt.year
    df = df.drop(['INSR_BEGIN', 'INSR_END'], axis=1)
    df = df.merge(veh, on='VEHICLE_ID', how='inner')
    df = df[['CUSTOMER_SENIORITY', 'SEX', 'INSR_TYPE', 'INSURED_VALUE', 'PREMIUM', 'PROD_YEAR', 'SEATS_NUM', 'CARRYING_CAPACITY', 'CCM_TON', 'MONTH_BEGIN', 'MONTH_END', 'YEAR_BEGIN', 'YEAR_END']].copy()
    df['SEX'] = np.where(df['SEX'] == 'Male', 1, np.where(df['SEX'] == 'Female', 0, pd.NA)).astype(int)

    return df


def run_batch(df):
    indexes = df.index
    batch = [v for v in df.T.to_dict().values()]
    predictions = requests.post('http://localhost:8000/predict_batch', json=batch)

    return pd.DataFrame(predictions.json(), index=indexes)


def run_stream(df):
    item = df.to_dict()
    prediction = requests.post('http://localhost:8000/predict_item', json=item)

    return prediction.json()


def main():
    dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(dir, 'test.csv')
    df = pd.read_csv(path)
    df = preprocess_df(df).fillna(-999)  # Visto que no puedo utilizar nans en JSON y que todos mis valores o son categoricos o son positivos, utilizo el -999 como codigo de nan

    logger.info('Testing batch.')
    batch_predictions = run_batch(df)
    pred_path = os.path.join(dir, 'predictions.csv')
    batch_predictions.to_csv(pred_path)
    logger.info(f'Batch predictions: {batch_predictions.head()}')

    logger.info('Testing stream.')
    item_prediction = run_stream(df.iloc[47])
    logger.info(f'Item prediction: {item_prediction}')


if __name__ == '__main__':
    main()
