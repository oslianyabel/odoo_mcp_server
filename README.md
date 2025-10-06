# Odoo MCP Server

Un servidor MCP (Model Context Protocol) que expone herramientas completas de gestión de Odoo para integración con asistentes de IA.

## 🚀 Características

Este servidor MCP proporciona acceso a todas las funcionalidades principales de Odoo a través de herramientas MCP:

### 👥 Gestión de Partners
- `create_partner` - Crear nuevos partners (clientes/proveedores)
- `get_partner` - Obtener información de partners por ID, teléfono o email

### 🎯 Gestión de Leads
- `create_lead` - Crear nuevas oportunidades en CRM

### 📋 Gestión de Pedidos de Venta
- `create_sale_order_by_product_id` - Crear pedido de venta con un producto específico
- `get_sale_orders_by_partner` - Obtener pedidos por partner
- `get_sale_orders_by_marketplace` - Obtener pedidos por marketplace
- `get_sale_order_by_name` - Buscar pedidos por nombre/referencia
- `get_sale_order_by_id` - Obtener pedido por ID

### 📦 Gestión de Productos
- `get_all_products` - Obtener todos los productos activos
- `get_products_by_category_id` - Obtener productos por ID de categoría
- `get_products_by_category_name` - Obtener productos por nombre de categoría

### 📁 Gestión de Categorías
- `get_all_categories` - Obtener todas las categorías
- `get_category_by_id` - Obtener categoría por ID
- `get_categories_by_name` - Buscar categorías por nombre
- `get_categories_children` - Obtener categorías hijas
- `get_category_parent` - Obtener categoría padre

### 📊 Business Intelligence
- `get_pending_invoices` - Obtener facturas pendientes
- `get_top_customers` - Obtener mejores clientes
- `get_top_selling_products` - Obtener productos más vendidos
- `get_orders_by_date` - Obtener pedidos por rango de fechas

### 🎫 Gestión de Helpdesk
- `get_helpdesk_tickets` - Obtener tickets de soporte
- `create_helpdesk_ticket` - Crear nuevos tickets

### 📈 Gestión de Inventario
- `get_replenishment_info` - Obtener información de reabastecimiento

## 🛠️ Uso
Para integrar en editores con IA en local como *Cursor*, *Windsurf* o *VS-Code con Copilot* debe completar las variables de entorno de *odoo_mcp.json* y pegar el contenido en el archivo *mcp_config.json* de su editor

Para su uso con *OpenAI* el servidor debe estar ejecutandose con transporte *sse*