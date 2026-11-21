# Grid Parity LatAm

**¿Siguen siendo rentables la solar y la eólica en Brasil y Chile cuando se descuenta la energía vertida?**

App: **https://grid-parity-latam.onrender.com**

Proyecto de la asignatura Desarrollo de Aplicaciones para la Visualización de Datos
(ICAI, curso 2026-2027). Autor: Telmo Plaza Bezos.

## La idea

Comparar el LCOE de una planta con el precio medio del mercado ya no sirve para saber si
es rentable. En Brasil y Chile una parte creciente de la energía solar y eólica se vierte
por falta de red, y la que se vende lo hace en las horas de precio más bajo.

La app calcula, por país, tecnología y mes:

| Indicador | Definición |
|---|---|
| Precio capturado (USD/MWh) | Media del precio horario ponderada por la generación de la tecnología |
| Ratio de captura | Precio capturado / precio medio del mes |
| Tasa de vertimiento *v* | Energía vertida / (generada + vertida) |
| LCOE efectivo (USD/MWh) | LCOE / (1 − *v*): coste por MWh realmente vendido |
| Margen de paridad (USD/MWh) | Precio capturado − LCOE efectivo (> 0: hay paridad) |

y los proyecta a 2026-2028, contrastando la proyección con los datos reales de 2026 y con
previsiones públicas de terceros (Aurora, ONS, Coordinador, Wood Mackenzie).

## Resultados principales (2022-2025)

- **Eólica en Chile**: la única con paridad a precio de mercado todos los años, aunque el
  margen cae de +64 USD/MWh (2022) a +9 (2024) y +21 (2025).
- **Solar en Chile**: en el norte (Crucero 220 kV) captura entre el 14 % y el 33 % del precio
  medio, porque a mediodía el costo marginal cae a cero. Margen de −43 USD/MWh en 2025.
- **Brasil**: sin paridad a precio spot en ningún año (eólica −7 y solar −30 USD/MWh en 2025).
  El PLD estuvo casi siempre en el suelo en 2022-2023 y el vertimiento solar llegó al 25 % en 2025.

## Datos (todos públicos)

| Dato | Brasil | Chile |
|---|---|---|
| Precio horario | CMO semihorario del ONS acotado a los límites del PLD (ANEEL) | Costo marginal real del Coordinador Eléctrico Nacional (API hasta jul-2024; después, descarga del visor) |
| Generación y vertimiento | ONS, constrained-off por central (eólica desde 2021, solar desde abr-2024) | Generación horaria por tecnología (API del Coordinador) y reducciones ERV mensuales (Excel oficial) |
| Tipo de cambio | PTAX, Banco Central do Brasil | No aplica (USD) |
| LCOE | IRENA, media mundial ponderada | IRENA, media mundial ponderada |

Por qué el CMO del ONS y no el PLD de la CCEE: el portal de la CCEE bloquea descargas
automatizadas. El PLD horario sale del mismo modelo (DESSEM) y se reconstruye acotando el
CMO entre el PLD mínimo y máximo de cada año.

Validaciones: el vertimiento calculado cuadra con las cifras publicadas (Brasil 2025 ≈ 20 %
frente al 20,7 % de S&P Global; Chile 2024: 5.642 GWh, igual que Ember).

## Modelo

- Para cada serie (país × tecnología × variable) se comparan tres candidatos: estacional
  ingenuo, ETS sin tendencia y ETS con tendencia amortiguada.
- Entrenamiento 2022-2024, validación fuera de muestra en 2025 (MAE).
- Se elige el modelo más simple cuyo MAE no supere en más de un 5 % al mejor (parsimonia).
- Proyección a 36 meses con intervalo del 80 %. LCOE con tendencia log-lineal.
- Contraste con lo real de 2026 (Brasil, ene-oct): el vertimiento se proyecta bien; el
  precio acierta la media pero no el perfil mensual, que depende de la hidrología.

## Limitaciones

- El LCOE es la media mundial ponderada de IRENA, no el de cada país.
- Solar en Brasil: solo hay datos desde abril de 2024, así que no se puede validar fuera de muestra.
- Chile: precio en una barra representativa por tecnología (Crucero para solar, Charrúa para eólica).
- El modelo es univariante: no incluye hidrología, nueva transmisión ni baterías.

## Estructura del código

```
app.py                  punto de entrada (local y Render)
src/config.py           rutas, países, tecnologías y colores
src/data.py             carga de los CSV procesados
src/indicators.py       ratio de captura, LCOE efectivo y margen
src/lcoe.py             LCOE anual de IRENA
src/model.py            selección de modelo, validación y proyección
src/figures.py          gráficos Plotly
src/layout.py           estructura de la página
src/callbacks.py        interactividad
src/sources/            descarga y limpieza por fuente (ons, brasil_precio, brasil, chile)
scripts/                construcción del dataset, del modelo y del contraste 2026
data/processed/         CSV que lee la app
data/external/          archivos descargados a mano y previsiones de terceros
assets/style.css        estilos
```

## Cómo ejecutar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                      # http://127.0.0.1:8050
```

Regenerar datos y modelo (descarga de las fuentes, unos minutos):

```bash
pip install -r requirements-dev.txt
python -m scripts.build_dataset
python -m scripts.build_forecast
python -m scripts.backtest_2026
```

La app desplegada solo lee `data/processed/`, así que arranca rápido y no depende de que las
fuentes estén disponibles.
