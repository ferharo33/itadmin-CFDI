# Lista de Verificación - cfdi_global_invoice

## ✓ Estructura del Módulo Completada

```
cfdi_global_invoice/
├── __init__.py                              ✓ Creado
├── __manifest__.py                          ✓ Creado
├── README.md                                ✓ Creado
├── models/
│   ├── __init__.py                          ✓ Creado
│   └── sale_order.py                        ✓ Creado
├── wizard/
│   ├── __init__.py                          ✓ Creado
│   ├── sale_create_global_invoice.py       ✓ Creado
│   └── sale_create_global_invoice_view.xml ✓ Creado
├── views/
│   └── sale_order_view.xml                 ✓ Creado
├── security/
│   └── ir.model.access.csv                 ✓ Creado
└── static/
    └── description/
        ├── icon.png                         ✓ Creado
        └── index.html                       ✓ Creado
```

## ✓ Archivos Python - Sintaxis Validada

- [x] `__init__.py` - Importa models y wizard
- [x] `__manifest__.py` - Configuración completa del módulo
- [x] `models/sale_order.py` - Extiende sale.order con campos is_global_invoice y global_invoice_id
- [x] `wizard/sale_create_global_invoice.py` - Lógica completa del wizard

## ✓ Archivos XML - Sintaxis Validada

- [x] `wizard/sale_create_global_invoice_view.xml` - Vista del wizard y acción
- [x] `views/sale_order_view.xml` - Hereda vistas de sale.order

## ✓ Modelo sale.order (models/sale_order.py)

- [x] Campo `is_global_invoice` (Boolean, readonly, no copy)
- [x] Campo `global_invoice_id` (Many2one a account.move, readonly, no copy)

## ✓ Wizard sale.create.global.invoice

### Campos:
- [x] `partner_id` (Many2one, requerido)
- [x] `date_invoice` (Date, default hoy, requerido)
- [x] `journal_id` (Many2one, requerido, domain sale)
- [x] `currency_id` (Many2one, computed, readonly)
- [x] `sale_order_count` (Integer, computed)

### Métodos:
- [x] `default_get()` - Establece valores por defecto
- [x] `_compute_currency_id()` - Obtiene moneda de pedidos
- [x] `_compute_sale_order_count()` - Cuenta pedidos seleccionados
- [x] `_get_sale_orders()` - Obtiene pedidos desde context
- [x] `_validate_sale_orders()` - Valida requisitos
- [x] `_group_lines_by_product()` - Agrupa y calcula precio promedio ponderado
- [x] `_prepare_global_invoice_values()` - Prepara valores de factura
- [x] `_mark_orders_as_invoiced()` - Marca pedidos y crea trazabilidad
- [x] `create_global_invoice()` - Método principal

## ✓ Validaciones Implementadas

- [x] Pedidos seleccionados no vacíos
- [x] Pedidos en estado 'sale' o 'done'
- [x] Pedidos no facturados (invoice_status != 'invoiced')
- [x] Misma moneda en todos los pedidos
- [x] Al menos una línea facturable

## ✓ Cálculo de Precio Promedio Ponderado

```python
# Implementación en _group_lines_by_product():
weighted_price += (line.price_unit * line.product_uom_qty)
quantity += line.product_uom_qty

# Luego:
price_unit = weighted_price / quantity
```

- [x] Acumula precio * cantidad
- [x] Suma cantidades
- [x] Divide para obtener promedio ponderado
- [x] Mismo cálculo para descuentos

## ✓ Vinculación de Líneas de Venta

- [x] Campo `sale_line_ids` en account.move.line
- [x] Permite trazabilidad nativa de Odoo
- [x] Actualiza automáticamente `invoice_status`

## ✓ Trazabilidad

- [x] Campo `is_global_invoice` en pedidos
- [x] Campo `global_invoice_id` en pedidos
- [x] Mensajes de seguimiento en pedidos
- [x] Mensaje de seguimiento en factura
- [x] Campo `invoice_origin` con lista de pedidos

## ✓ Campos CFDI (Condicionales)

- [x] Verifica existencia de campos antes de asignar
- [x] `tipo_comprobante` = 'I' (Ingreso)
- [x] `uso_cfdi` del cliente si existe
- [x] `metodo_pago` = 'PUE'
- [x] `forma_pago` del cliente si existe

## ✓ Seguridad

- [x] Permisos para sales_team.group_sale_salesman
- [x] Permisos para sales_team.group_sale_manager

## ✓ Acción del Wizard

- [x] `binding_model_id` = sale.model_sale_order
- [x] `binding_view_types` = list
- [x] Aparece en menú "Acción" en vista lista

## Pasos para Instalación y Prueba

1. **Actualizar lista de módulos**:
   ```bash
   # En Odoo: Apps → Actualizar lista de aplicaciones
   ```

2. **Instalar módulo**:
   ```bash
   # Buscar "CFDI Factura Global" e instalar
   ```

3. **Verificar permisos**:
   - Usuario debe tener rol de ventas (salesman o manager)

4. **Crear datos de prueba**:
   - Crear 3+ pedidos de venta con:
     - Mismo cliente (o diferentes)
     - Misma moneda
     - Estado confirmado (sale)
     - No facturados
     - Algunos con mismo producto a diferente precio

5. **Ejecutar wizard**:
   - Ir a Ventas → Pedidos → Pedidos de Venta
   - Seleccionar pedidos con checkbox
   - Acción → Crear Factura Global
   - Verificar wizard muestra información correcta
   - Crear factura

6. **Verificar resultado**:
   - Factura creada en borrador
   - Líneas agrupadas por producto
   - Cantidades sumadas
   - Precio promedio ponderado correcto
   - invoice_origin muestra todos los pedidos
   - Pedidos marcados: is_global_invoice = True
   - Pedidos vinculados: global_invoice_id apunta a factura
   - invoice_status = 'invoiced' en pedidos

7. **Verificar cálculo de precio promedio**:
   Ejemplo:
   - Pedido 1: Producto A, 10 unidades a $100 = $1,000
   - Pedido 2: Producto A, 5 unidades a $110 = $550
   - Total: 15 unidades
   - Precio promedio esperado: $1,550 / 15 = $103.33

## Archivos de Referencia Consultados

- `/home/fernando/projects/odoo-14/odoo/addons/sale/wizard/sale_make_invoice_advance.py`
- `/home/fernando/projects/odoo-14/odoo/addons/sale/models/sale.py`
- `/home/fernando/projects/odoo-14/odoo/addons/account/models/account_move.py`
- `/home/fernando/projects/odoo-14/itadmin-CFDI/multi_rfc_cfdi/`
- `/home/fernando/projects/odoo-14/itadmin-CFDI/cdfi_invoice/models/account_invoice.py`

## Estado: IMPLEMENTACIÓN COMPLETA ✓

Todos los archivos han sido creados según el plan de implementación.
Sintaxis Python y XML validada.
Listo para instalación y pruebas.
