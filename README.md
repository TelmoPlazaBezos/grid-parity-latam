# Grid Parity LatAm

Paridad de red en Brasil y Chile: LCOE efectivo frente a precio capturado.

Proyecto de la asignatura Desarrollo de Aplicaciones para la Visualización de Datos
(ICAI, curso 2026-2027). Autor: Telmo Plaza Bezos.

## Descripción

En Brasil y Chile una parte creciente de la energía solar y eólica se vierte por falta
de red, y la que se vende lo hace en las horas de precio más bajo. Comparar el LCOE con
el precio medio del mercado ya no sirve para saber si una planta es rentable.

Este proyecto calcula el coste real de cada tecnología, ajustado por la energía vertida,
y lo compara con el precio que de verdad captura en el mercado. Todo con datos públicos.

## Objetivos

1. Calcular cinco indicadores por mes, país y tecnología (solar fotovoltaica y eólica
   terrestre): precio capturado, ratio de captura, tasa de vertimiento, LCOE efectivo
   y margen.
2. Proyectar a tres años el precio capturado, el vertimiento y el LCOE, con bandas de
   confianza, y estimar en qué año cambia de signo el margen.
3. Publicar un dashboard interactivo en Dash, desplegado en Render.

## Datos

| Dato | Brasil | Chile |
|---|---|---|
| Precio horario | CCEE (PLD por submercado) | Coordinador Eléctrico Nacional (costo marginal real) |
| Generación y vertimiento | ONS | Coordinador Eléctrico Nacional / ACERA |
| LCOE | IRENA | IRENA |
| Tipo de cambio | Banco Central do Brasil (PTAX) | No aplica (USD) |

Los datos de CCEE y ONS se publican con licencia CC BY 4.0.

## Plan de trabajo

| Fase | Fechas | Entregable |
|---|---|---|
| 1. Datos | 6 – 25 oct 2026 | Descarga, limpieza e indicadores históricos 2022-2025 |
| 2. Modelo | 26 oct – 8 nov | Proyección a 3 años, validada con 2025 |
| 3. Dashboard | 9 – 19 nov | Aplicación en Dash |
| 4. Despliegue | 20 – 25 nov | Publicación en Render y README final |

## Estado

Propuesta presentada el 5 de octubre de 2026. Desarrollo en curso.

> **Nota:** este README recoge la propuesta tal y como está a 4 de octubre de 2026. Es un
> punto de partida, no un plan cerrado. A lo largo del cuatrimestre pueden surgir
> contratiempos con los datos o ideas nuevas que cambien el alcance, la metodología o el
> calendario. Cualquier cambio quedará reflejado aquí.
