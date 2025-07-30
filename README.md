# lc_api
## Endpoints
### /predict_item
Permite prediccion en Streaming.
Input: un JSON con la estructura definida por el Pydantic Policy, que contiene las columnas utilizadas en el modelo. 
Para llevar la fila del DF al JSON, usar .to_dict().
Output: un JSON con las predicciones, los ms que demoro la prediccion en su totalidad y la fecha de finalizacion de la prediccion.

### /predict_batch
Permite prediccion de batches.
Input: una lista de JSONs con la estructura definida por el Pydantic Policy, que contiene las columnas utilizadas en el modelo. 
Para llevar el DF a la estructura del JSON, se debe transponer el mismo, usar .to_dict() y generar una lista de todos los valores en el mismo.
Output: una lista de JSONs con las predicciones, los ms que demoro la prediccion en su totalidad (repetido por fila) y la fecha de finalizacion de la prediccion (repetida por fila).

## Ejecucion
Para poder ejecutar el container se debe:
1. Crear la imagen realizando `docker build lcapi .` en el directorio donde se encuentra el dockefile.
2. Correr un container utilizando la imagen realizando `docker run -p 8000:8000 lcapi`.

Para realizar los tests simplemente ejecute el `python tests.py` una vez levantado el container.

## Desarrollo
Al inicar el desarrollo de esta API comence con un brainstorming, donde considere que:
- Por cuestiones de performance el modelo deberia estar en memoria dentro del container.
- Debia realizar validacion de datos para que la prediccion sea robusta.
    - Esto podria ser delegado a la aplicacion consumidora de la API y que la API retorne error, pero por integridad decidi incorporarlo en la API.
- El container debia ser ligero y seguro, con lo minimo necesario para realizar la prediccion.
- Debia escalar para que si el modelo se encuentra demandado por el batch, aun pueda realizar tareas de streaming.

De acuerdo a esos pilares:
- Precargo en FastAPI el modelo en una variable para que este disponible.
- Creo un wrapper al modelo que incluya validacion.
- Unicamente copio aquello archivos requeridos a una imagen ligera de Python, a su vez, defino un usuario no root para delimitar los poderes en el container.
- Asigno 4 workers en Uvicorn, para facilitar disponibilidad.
    - Otra solucion podria haber sido asignar un hilo exclusivo al streaming o utilizar una cola asincronica de mensajes, pero por simplicidad se opto por escalado horizontal.