# lc_api
## Brainstorming
- Modelo en memoria del servicio para que responda rapido, en inicializacion del container?
- Asincronico para poder gestionar batch y streaming, necesito dos instancias del modelo o una sola puede gestionarlo?
- Convendria que sea algo de caracter distribuido?
- Quien es mi consumidor? Que tanta info necesita que la API le devuelva? Parametrizar distintos niveles o consultar
- Como hago que el servicio sea resiliente si se cae? Tengo que tenerlo en cuenta?
- Validacion de datos, que respuesta se espera? Error o que pase igual o que se procese?
- Me interesa guardar los datos enviados de alguna forma? Cache?
- Sirve tener algun endpoint de ayuda? Como para entender que formato espera la API
- Prestar atencion a seguridad de la API

## Idea
