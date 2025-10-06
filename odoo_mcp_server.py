import json
from typing import Optional

from fastmcp import FastMCP, Context

from odoo_manager import odoo_manager

# Initialize MCP server
mcp = FastMCP("OdooServer")

# ============================
# Partner Management Tools
# ============================


@mcp.tool
async def create_partner(
    name: str, phone: str, email: Optional[str] = None, ctx: Context = None
) -> str:
    """
    Create a new partner (customer/supplier) in Odoo.

    Args:
        name: Partner name
        phone: Partner phone number
        email: Partner email (optional)

    Returns:
        Dictionary containing partner information and creation status
    """
    await ctx.info(f"Ejecutando create_partner con name={name}, phone={phone}, email={email}")
    try:
        partner, status = await odoo_manager.create_partner(name, phone, email)
        await ctx.info(f"Partner creado exitosamente: {partner.get('name', 'N/A')}")
        return json.dumps({"partner": partner, "status": status, "success": True})
    except Exception as e:
        await ctx.error(f"Error creating partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_partner(
    partner_id: Optional[int] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    Get partner information by ID, phone, or email.

    Args:
        partner_id: Partner ID
        phone: Partner phone number
        email: Partner email

    Returns:
        Dictionary containing partner information
    """
    await ctx.info(f"Ejecutando get_partner con partner_id={partner_id}, phone={phone}, email={email}")
    try:
        if partner_id:
            partner = await odoo_manager.get_partner_by_id(partner_id)
        elif phone:
            partner = await odoo_manager.get_partner_by_phone(phone)
        elif email:
            partner = await odoo_manager.get_partner_by_email(email)
        else:
            await ctx.warning("No se proporcionó partner_id, phone o email")
            return json.dumps({
                "success": False,
                "error": "Must provide partner_id, phone, or email",
            })

        await ctx.info(f"Partner encontrado: {partner.get('name', 'N/A') if partner else 'No encontrado'}")
        return json.dumps({"partner": partner, "success": True})
    except Exception as e:
        await ctx.error(f"Error getting partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Lead Management Tools
# ============================


@mcp.tool
async def create_lead(partner_id: int, resume: str, email: str, ctx: Context = None) -> str:
    """
    Create a new lead/opportunity in Odoo CRM.

    Args:
        partner_id: Partner ID for the lead
        resume: Lead description/resume
        email: Contact email

    Returns:
        Dictionary containing lead information
    """
    await ctx.info(f"Ejecutando create_lead con partner_id={partner_id}")
    try:
        # Get partner info first
        partner = await odoo_manager.get_partner_by_id(partner_id)
        if not partner:
            await ctx.error(f"Partner con ID {partner_id} no encontrado")
            return json.dumps({
                "success": False,
                "error": f"Partner with ID {partner_id} not found",
            })

        lead = await odoo_manager.create_lead(partner, resume, email)
        await ctx.info("Lead creado exitosamente")
        return json.dumps({"lead": lead, "success": True})
    except Exception as e:
        await ctx.error(f"Error creating lead: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Sale Order Management Tools
# ============================


@mcp.tool
async def create_sale_order_by_product_id(
    partner_id: int, product_id: int, quantity: int = 1, ctx: Context = None
) -> str:
    """
    Create a sale order with a single product by product ID.

    Args:
        partner_id: Customer partner ID
        product_id: Product ID to add to the order
        quantity: Product quantity (default: 1)

    Returns:
        Dictionary containing sale order information
    """
    await ctx.info(f"Ejecutando create_sale_order_by_product_id con partner_id={partner_id}, product_id={product_id}, quantity={quantity}")
    try:
        order = await odoo_manager.create_sale_order_by_product_id(
            partner_id, product_id, quantity
        )
        await ctx.info("Orden de venta creada exitosamente")
        return json.dumps({"sale_order": order, "success": True})
    except Exception as e:
        await ctx.error(f"Error creating sale order: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_orders_by_partner(partner_id: int, ctx: Context = None) -> str:
    """
    Get all sale orders for a specific partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of sale orders
    """
    await ctx.info(f"Ejecutando get_sale_orders_by_partner con partner_id={partner_id}")
    try:
        orders = await odoo_manager.get_sale_orders_by_partner(partner_id)
        await ctx.info(f"Se encontraron {len(orders) if orders else 0} órdenes de venta")
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting sale orders by partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_orders_by_marketplace(marketplace: str, ctx: Context = None) -> str:
    """
    Get sale orders filtered by marketplace.

    Args:
        marketplace: Marketplace name to filter by

    Returns:
        Dictionary containing list of sale orders
    """
    await ctx.info(f"Ejecutando get_sale_orders_by_marketplace con marketplace={marketplace}")
    try:
        orders = await odoo_manager.get_sale_orders_by_marketplace(marketplace)
        await ctx.info(f"Se encontraron {len(orders) if orders else 0} órdenes del marketplace {marketplace}")
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting sale orders by marketplace: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_order_by_name(name: str, ctx: Context = None) -> str:
    """
    Get sale orders by name/reference.

    Args:
        name: Order name or reference to search for

    Returns:
        Dictionary containing list of matching sale orders
    """
    await ctx.info(f"Ejecutando get_sale_order_by_name con name={name}")
    try:
        orders = await odoo_manager.get_sale_order_by_name(name)
        await ctx.info(f"Se encontraron {len(orders) if orders else 0} órdenes con nombre '{name}'")
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting sale order by name: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_order_by_id(order_id: int, ctx: Context = None) -> str:
    """
    Get sale order by ID.

    Args:
        order_id: Sale order ID

    Returns:
        Dictionary containing sale order information
    """
    await ctx.info(f"Ejecutando get_sale_order_by_id con order_id={order_id}")
    try:
        orders = await odoo_manager.get_sale_order_by_id(order_id)
        await ctx.info(f"Orden {'encontrada' if orders else 'no encontrada'}")
        return json.dumps({"sale_order": orders[0] if orders else None, "success": True})
    except Exception as e:
        await ctx.error(f"Error getting sale order by ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Product Management Tools
# ============================


@mcp.tool
async def get_all_products(ctx: Context = None) -> str:
    """
    Get all active products from Odoo.

    Returns:
        Dictionary containing list of all products
    """
    await ctx.info("Ejecutando get_all_products")
    try:
        products = await odoo_manager.get_all_products()
        await ctx.info(f"Se encontraron {len(products) if products else 0} productos")
        return json.dumps({
            "products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting all products: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_products_by_category_id(category_id: int, ctx: Context = None) -> str:
    """
    Get products by category ID.

    Args:
        category_id: Product category ID

    Returns:
        Dictionary containing list of products in the category
    """
    await ctx.info(f"Ejecutando get_products_by_category_id con category_id={category_id}")
    try:
        products = await odoo_manager.get_products_by_category_id(category_id)
        await ctx.info(f"Se encontraron {len(products) if products else 0} productos en la categoría {category_id}")
        return json.dumps({
            "products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting products by category ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_products_by_category_name(category_name: str, ctx: Context = None) -> str:
    """
    Get products by category name.

    Args:
        category_name: Product category name

    Returns:
        Dictionary containing products grouped by category
    """
    await ctx.info(f"Ejecutando get_products_by_category_name con category_name={category_name}")
    try:
        products = await odoo_manager.get_products_by_category_name(category_name)
        await ctx.info(f"Productos obtenidos por categoría '{category_name}'")
        return json.dumps({"products_by_category": products or {}, "success": True})
    except Exception as e:
        await ctx.error(f"Error getting products by category name: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Category Management Tools
# ============================


@mcp.tool
async def get_all_categories(ctx: Context = None) -> str:
    """
    Get all product categories from Odoo.

    Returns:
        Dictionary containing list of all categories
    """
    await ctx.info("Ejecutando get_all_categories")
    try:
        categories = await odoo_manager.get_all_categories()
        await ctx.info(f"Se encontraron {len(categories) if categories else 0} categorías")
        return json.dumps({
            "categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting all categories: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_category_by_id(category_id: int, ctx: Context = None) -> str:
    """
    Get category by ID.

    Args:
        category_id: Category ID

    Returns:
        Dictionary containing category information
    """
    await ctx.info(f"Ejecutando get_category_by_id con category_id={category_id}")
    try:
        categories = await odoo_manager.get_category_by_id(category_id)
        await ctx.info(f"Categoría {'encontrada' if categories else 'no encontrada'}")
        return json.dumps({"category": categories[0] if categories else None, "success": True})
    except Exception as e:
        await ctx.error(f"Error getting category by ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_categories_by_name(name: str, ctx: Context = None) -> str:
    """
    Get categories by name.

    Args:
        name: Category name to search for

    Returns:
        Dictionary containing list of matching categories
    """
    await ctx.info(f"Ejecutando get_categories_by_name con name={name}")
    try:
        categories = await odoo_manager.get_categories_by_name(name)
        await ctx.info(f"Se encontraron {len(categories) if categories else 0} categorías con nombre '{name}'")
        return json.dumps({
            "categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting categories by name: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_categories_children(parent_id: int, ctx: Context = None) -> str:
    """
    Get child categories of a parent category.

    Args:
        parent_id: Parent category ID

    Returns:
        Dictionary containing list of child categories
    """
    await ctx.info(f"Ejecutando get_categories_children con parent_id={parent_id}")
    try:
        categories = await odoo_manager.get_categories_children(parent_id)
        await ctx.info(f"Se encontraron {len(categories) if categories else 0} subcategorías")
        return json.dumps({
            "child_categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting child categories: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_category_parent(child_id: int, ctx: Context = None) -> str:
    """
    Get parent category of a child category.

    Args:
        child_id: Child category ID

    Returns:
        Dictionary containing parent category information
    """
    await ctx.info(f"Ejecutando get_category_parent con child_id={child_id}")
    try:
        categories = await odoo_manager.get_category_parent(child_id)
        await ctx.info(f"Categoría padre {'encontrada' if categories else 'no encontrada'}")
        return json.dumps({
            "parent_categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting parent category: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Business Intelligence Tools
# ============================


@mcp.tool
async def get_pending_invoices(partner_id: int, ctx: Context = None) -> str:
    """
    Get pending invoices for a partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of pending invoices
    """
    await ctx.info(f"Ejecutando get_pending_invoices con partner_id={partner_id}")
    try:
        invoices = await odoo_manager.get_pending_invoices(partner_id)
        await ctx.info(f"Se encontraron {len(invoices) if invoices else 0} facturas pendientes")
        return json.dumps({
            "pending_invoices": invoices or [],
            "count": len(invoices) if invoices else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting pending invoices: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_top_customers(
    date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10, ctx: Context = None
) -> str:
    """
    Get top customers by sales amount.

    Args:
        date_from: Start date (YYYY-MM-DD format, optional)
        date_to: End date (YYYY-MM-DD format, optional)
        limit: Maximum number of customers to return (default: 10)

    Returns:
        Dictionary containing list of top customers
    """
    await ctx.info(f"Ejecutando get_top_customers con date_from={date_from}, date_to={date_to}, limit={limit}")
    try:
        customers = await odoo_manager.get_top_customers(date_from, date_to, limit)
        await ctx.info(f"Se encontraron {len(customers) if customers else 0} clientes top")
        return json.dumps({
            "top_customers": customers or [],
            "count": len(customers) if customers else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting top customers: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_top_selling_products(
    date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10, ctx: Context = None
) -> str:
    """
    Get top selling products by quantity.

    Args:
        date_from: Start date (YYYY-MM-DD format, optional)
        date_to: End date (YYYY-MM-DD format, optional)
        limit: Maximum number of products to return (default: 10)

    Returns:
        Dictionary containing list of top selling products
    """
    await ctx.info(f"Ejecutando get_top_selling_products con date_from={date_from}, date_to={date_to}, limit={limit}")
    try:
        products = await odoo_manager.get_top_selling_products(
            date_from, date_to, limit
        )
        await ctx.info(f"Se encontraron {len(products) if products else 0} productos más vendidos")
        return json.dumps({
            "top_selling_products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting top selling products: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_orders_by_date(date_from: str, date_to: str, ctx: Context = None) -> str:
    """
    Get orders within a date range.

    Args:
        date_from: Start date (YYYY-MM-DD format)
        date_to: End date (YYYY-MM-DD format)

    Returns:
        Dictionary containing list of orders in the date range
    """
    await ctx.info(f"Ejecutando get_orders_by_date con date_from={date_from}, date_to={date_to}")
    try:
        orders = await odoo_manager.get_orders_by_date(date_from, date_to)
        await ctx.info(f"Se encontraron {len(orders) if orders else 0} órdenes en el rango de fechas")
        return json.dumps({
            "orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting orders by date: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Helpdesk Tools
# ============================


@mcp.tool
async def get_helpdesk_tickets(partner_id: int, ctx: Context = None) -> str:
    """
    Get helpdesk tickets for a partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of helpdesk tickets
    """
    await ctx.info(f"Ejecutando get_helpdesk_tickets con partner_id={partner_id}")
    try:
        tickets = await odoo_manager.get_helpdesk_tickets(partner_id)
        await ctx.info(f"Se encontraron {len(tickets) if tickets else 0} tickets de soporte")
        return json.dumps({
            "helpdesk_tickets": tickets or [],
            "count": len(tickets) if tickets else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting helpdesk tickets: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def create_helpdesk_ticket(
    partner_id: int, name: str, description: Optional[str] = None, ctx: Context = None
) -> str:
    """
    Create a new helpdesk ticket.

    Args:
        partner_id: Partner ID for the ticket
        name: Ticket title/name
        description: Ticket description (optional)

    Returns:
        Dictionary containing ticket information
    """
    await ctx.info(f"Ejecutando create_helpdesk_ticket con partner_id={partner_id}, name={name}")
    try:
        ticket = await odoo_manager.create_helpdesk_ticket(
            partner_id, name, description
        )
        await ctx.info("Ticket de soporte creado exitosamente")
        return json.dumps({"helpdesk_ticket": ticket, "success": True})
    except Exception as e:
        await ctx.error(f"Error creating helpdesk ticket: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Inventory/Replenishment Tools
# ============================


@mcp.tool
async def get_replenishment_info(product_id: Optional[int] = None, ctx: Context = None) -> str:
    """
    Get replenishment/procurement information.

    Args:
        product_id: Product ID to get replenishment info for (optional, gets all if not specified)

    Returns:
        Dictionary containing replenishment information
    """
    await ctx.info(f"Ejecutando get_replenishment_info con product_id={product_id}")
    try:
        replenishments = await odoo_manager.get_replenishment_info(product_id)
        await ctx.info(f"Se encontraron {len(replenishments) if replenishments else 0} registros de reabastecimiento")
        return json.dumps({
            "replenishment_info": replenishments or [],
            "count": len(replenishments) if replenishments else 0,
            "success": True,
        })
    except Exception as e:
        await ctx.error(f"Error getting replenishment info: {e}")
        return json.dumps({"success": False, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
