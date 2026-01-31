# CFDI Factura Global

Módulo para Odoo 14 que permite generar facturas globales CFDI desde múltiples pedidos de venta.

## Características

- **Selección Múltiple**: Seleccione varios pedidos de venta confirmados y genere una sola factura global
- **Agrupación Inteligente**: Los productos iguales se agrupan automáticamente, sumando cantidades
- **Precio Promedio Ponderado**: Calcula el precio promedio ponderado cuando se agrupan productos con diferentes precios
- **Validaciones Robustas**: Verifica que todos los pedidos tengan la misma moneda, estén confirmados y no facturados
- **Trazabilidad Completa**: Mantiene la relación entre pedidos y factura, con mensajes de seguimiento

## Instalación

1. Copie el módulo en el directorio de addons de Odoo
2. Actualice la lista de aplicaciones: Apps → Actualizar lista de aplicaciones
3. Busque "CFDI Factura Global" e instale el módulo

## Uso

1. Vaya a **Ventas → Pedidos → Pedidos de Venta**
2. Seleccione múltiples pedidos confirmados (use los checkboxes)
3. Haga clic en **Acción → Crear Factura Global**
4. En el wizard:
   - Verifique/seleccione el cliente
   - Ajuste la fecha si es necesario
   - Revise el diario y moneda
5. Haga clic en **Crear Factura Global**
6. Se abrirá la factura en borrador, lista para timbrar

## Validaciones

El módulo valida que:

- Los pedidos deben estar confirmados (estado: Venta o Hecho)
- No deben estar previamente facturados
- Todos deben tener la misma moneda
- Deben tener al menos una línea facturable

## Cálculo de Precio Promedio Ponderado

Cuando se agrupan productos del mismo tipo pero con diferentes precios, el módulo calcula:

```
precio_promedio = Σ(precio_unitario × cantidad) / Σ(cantidad)
```

Por ejemplo, si tiene:
- Producto A: 10 unidades a $100
- Producto A: 5 unidades a $110

El precio promedio será:
```
(10 × 100 + 5 × 110) / (10 + 5) = (1000 + 550) / 15 = $103.33
```

## Dependencias

- base
- sale
- account
- cdfi_invoice

## Compatibilidad

- Odoo 14.0

## Autor

**Teamfactory**
- Website: https://teamfactory.mx

## Licencia

LGPL-3
