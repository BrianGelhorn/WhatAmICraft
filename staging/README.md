# Entorno de desarrollo aislado

Este compose usa el proyecto `minecraftquizguesser-dev`, los puertos `8788` y `8081`, y volúmenes propios.

Por seguridad, `bot` y `publisher-worker` están detrás del perfil `integrations` y no tienen credenciales. El stack productivo no comparte contenedores, red, puertos, datos ni secretos con este entorno.
