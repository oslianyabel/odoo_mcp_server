import json
from typing import Optional

from fastmcp import FastMCP

from odoo_manager import odoo_manager

# Initialize MCP server
mcp = FastMCP("OdooServer")

# ============================
# Partner Management Tools
# ============================


@mcp.tool
async def create_partner(
    name: str, phone: str, email: Optional[str] = None
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
    print(f"[TOOL] create_partner - Ejecutando con name={name}, phone={phone}, email={email}")
    try:
        partner, status = await odoo_manager.create_partner(name, phone, email)
        return json.dumps({"partner": partner, "status": status, "success": True})
    except Exception as e:
        print(f"Error creating partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_partner(
    partner_id: Optional[int] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
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
    print(f"[TOOL] get_partner - Ejecutando con partner_id={partner_id}, phone={phone}, email={email}")
    try:
        if partner_id:
            partner = await odoo_manager.get_partner_by_id(partner_id)
        elif phone:
            partner = await odoo_manager.get_partner_by_phone(phone)
        elif email:
            partner = await odoo_manager.get_partner_by_email(email)
        else:
            return json.dumps({
                "success": False,
                "error": "Must provide partner_id, phone, or email",
            })

        return json.dumps({"partner": partner, "success": True})
    except Exception as e:
        print(f"Error getting partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Lead Management Tools
# ============================


@mcp.tool
async def create_lead(partner_id: int, resume: str, email: str) -> str:
    """
    Create a new lead/opportunity in Odoo CRM.

    Args:
        partner_id: Partner ID for the lead
        resume: Lead description/resume
        email: Contact email

    Returns:
        Dictionary containing lead information
    """
    print(f"[TOOL] create_lead - Ejecutando con partner_id={partner_id}, resume={resume}, email={email}")
    try:
        # Get partner info first
        partner = await odoo_manager.get_partner_by_id(partner_id)
        if not partner:
            return json.dumps({
                "success": False,
                "error": f"Partner with ID {partner_id} not found",
            })

        lead = await odoo_manager.create_lead(partner, resume, email)
        return json.dumps({"lead": lead, "success": True})
    except Exception as e:
        print(f"Error creating lead: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Sale Order Management Tools
# ============================


@mcp.tool
async def create_sale_order_by_product_id(
    partner_id: int, product_id: int, quantity: int = 1
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
    print(f"[TOOL] create_sale_order_by_product_id - Ejecutando con partner_id={partner_id}, product_id={product_id}, quantity={quantity}")
    try:
        order = await odoo_manager.create_sale_order_by_product_id(
            partner_id, product_id, quantity
        )
        return json.dumps({"sale_order": order, "success": True})
    except Exception as e:
        print(f"Error creating sale order: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_orders_by_partner(partner_id: int) -> str:
    """
    Get all sale orders for a specific partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of sale orders
    """
    print(f"[TOOL] get_sale_orders_by_partner - Ejecutando con partner_id={partner_id}")
    try:
        orders = await odoo_manager.get_sale_orders_by_partner(partner_id)
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting sale orders by partner: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_orders_by_marketplace(marketplace: str) -> str:
    """
    Get sale orders filtered by marketplace.

    Args:
        marketplace: Marketplace name to filter by

    Returns:
        Dictionary containing list of sale orders
    """
    print(f"[TOOL] get_sale_orders_by_marketplace - Ejecutando con marketplace={marketplace}")
    try:
        orders = await odoo_manager.get_sale_orders_by_marketplace(marketplace)
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting sale orders by marketplace: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_order_by_name(name: str) -> str:
    """
    Get sale orders by name/reference.

    Args:
        name: Order name or reference to search for

    Returns:
        Dictionary containing list of matching sale orders
    """
    print(f"[TOOL] get_sale_order_by_name - Ejecutando con name={name}")
    try:
        orders = await odoo_manager.get_sale_order_by_name(name)
        return json.dumps({
            "sale_orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting sale order by name: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_sale_order_by_id(order_id: int) -> str:
    """
    Get sale order by ID.

    Args:
        order_id: Sale order ID

    Returns:
        Dictionary containing sale order information
    """
    print(f"[TOOL] get_sale_order_by_id - Ejecutando con order_id={order_id}")
    try:
        orders = await odoo_manager.get_sale_order_by_id(order_id)
        return json.dumps({"sale_order": orders[0] if orders else None, "success": True})
    except Exception as e:
        print(f"Error getting sale order by ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Product Management Tools
# ============================


@mcp.tool
async def get_all_products() -> str:
    """
    Get all active products from Odoo.

    Returns:
        Dictionary containing list of all products
    """
    print("[TOOL] get_all_products - Ejecutando")
    try:
        products = await odoo_manager.get_all_products()
        return json.dumps({
            "products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting all products: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_products_by_category_id(category_id: int) -> str:
    """
    Get products by category ID.

    Args:
        category_id: Product category ID

    Returns:
        Dictionary containing list of products in the category
    """
    print(f"[TOOL] get_products_by_category_id - Ejecutando con category_id={category_id}")
    try:
        products = await odoo_manager.get_products_by_category_id(category_id)
        return json.dumps({
            "products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting products by category ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_products_by_category_name(category_name: str) -> str:
    """
    Get products by category name.

    Args:
        category_name: Product category name

    Returns:
        Dictionary containing products grouped by category
    """
    print(f"[TOOL] get_products_by_category_name - Ejecutando con category_name={category_name}")
    try:
        products = await odoo_manager.get_products_by_category_name(category_name)
        return json.dumps({"products_by_category": products or {}, "success": True})
    except Exception as e:
        print(f"Error getting products by category name: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Category Management Tools
# ============================


@mcp.tool
async def get_all_categories() -> str:
    """
    Get all product categories from Odoo.

    Returns:
        Dictionary containing list of all categories
    """
    print("[TOOL] get_all_categories - Ejecutando")
    try:
        categories = await odoo_manager.get_all_categories()
        return json.dumps({
            "categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting all categories: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_category_by_id(category_id: int) -> str:
    """
    Get category by ID.

    Args:
        category_id: Category ID

    Returns:
        Dictionary containing category information
    """
    print(f"[TOOL] get_category_by_id - Ejecutando con category_id={category_id}")
    try:
        categories = await odoo_manager.get_category_by_id(category_id)
        return json.dumps({"category": categories[0] if categories else None, "success": True})
    except Exception as e:
        print(f"Error getting category by ID: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_categories_by_name(name: str) -> str:
    """
    Get categories by name.

    Args:
        name: Category name to search for

    Returns:
        Dictionary containing list of matching categories
    """
    print(f"[TOOL] get_categories_by_name - Ejecutando con name={name}")
    try:
        categories = await odoo_manager.get_categories_by_name(name)
        return json.dumps({
            "categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting categories by name: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_categories_children(parent_id: int) -> str:
    """
    Get child categories of a parent category.

    Args:
        parent_id: Parent category ID

    Returns:
        Dictionary containing list of child categories
    """
    print(f"[TOOL] get_categories_children - Ejecutando con parent_id={parent_id}")
    try:
        categories = await odoo_manager.get_categories_children(parent_id)
        return json.dumps({
            "child_categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting child categories: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_category_parent(child_id: int) -> str:
    """
    Get parent category of a child category.

    Args:
        child_id: Child category ID

    Returns:
        Dictionary containing parent category information
    """
    print(f"[TOOL] get_category_parent - Ejecutando con child_id={child_id}")
    try:
        categories = await odoo_manager.get_category_parent(child_id)
        return json.dumps({
            "parent_categories": categories or [],
            "count": len(categories) if categories else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting parent category: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Business Intelligence Tools
# ============================


@mcp.tool
async def get_pending_invoices(partner_id: int) -> str:
    """
    Get pending invoices for a partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of pending invoices
    """
    print(f"[TOOL] get_pending_invoices - Ejecutando con partner_id={partner_id}")
    try:
        invoices = await odoo_manager.get_pending_invoices(partner_id)
        return json.dumps({
            "pending_invoices": invoices or [],
            "count": len(invoices) if invoices else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting pending invoices: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_top_customers(
    date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10
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
    print(f"[TOOL] get_top_customers - Ejecutando con date_from={date_from}, date_to={date_to}, limit={limit}")
    try:
        customers = await odoo_manager.get_top_customers(date_from, date_to, limit)
        return json.dumps({
            "top_customers": customers or [],
            "count": len(customers) if customers else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting top customers: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_top_selling_products(
    date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10
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
    print(f"[TOOL] get_top_selling_products - Ejecutando con date_from={date_from}, date_to={date_to}, limit={limit}")
    try:
        products = await odoo_manager.get_top_selling_products(
            date_from, date_to, limit
        )
        return json.dumps({
            "top_selling_products": products or [],
            "count": len(products) if products else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting top selling products: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def get_orders_by_date(date_from: str, date_to: str) -> str:
    """
    Get orders within a date range.

    Args:
        date_from: Start date (YYYY-MM-DD format)
        date_to: End date (YYYY-MM-DD format)

    Returns:
        Dictionary containing list of orders in the date range
    """
    print(f"[TOOL] get_orders_by_date - Ejecutando con date_from={date_from}, date_to={date_to}")
    try:
        orders = await odoo_manager.get_orders_by_date(date_from, date_to)
        return json.dumps({
            "orders": orders or [],
            "count": len(orders) if orders else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting orders by date: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Helpdesk Tools
# ============================


@mcp.tool
async def get_helpdesk_tickets(partner_id: int) -> str:
    """
    Get helpdesk tickets for a partner.

    Args:
        partner_id: Partner ID

    Returns:
        Dictionary containing list of helpdesk tickets
    """
    print(f"[TOOL] get_helpdesk_tickets - Ejecutando con partner_id={partner_id}")
    try:
        tickets = await odoo_manager.get_helpdesk_tickets(partner_id)
        return json.dumps({
            "helpdesk_tickets": tickets or [],
            "count": len(tickets) if tickets else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting helpdesk tickets: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool
async def create_helpdesk_ticket(
    partner_id: int, name: str, description: Optional[str] = None
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
    print(f"[TOOL] create_helpdesk_ticket - Ejecutando con partner_id={partner_id}, name={name}, description={description}")
    try:
        ticket = await odoo_manager.create_helpdesk_ticket(
            partner_id, name, description
        )
        return json.dumps({"helpdesk_ticket": ticket, "success": True})
    except Exception as e:
        print(f"Error creating helpdesk ticket: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================
# Inventory/Replenishment Tools
# ============================


@mcp.tool
async def get_replenishment_info(product_id: Optional[int] = None) -> str:
    """
    Get replenishment/procurement information.

    Args:
        product_id: Product ID to get replenishment info for (optional, gets all if not specified)

    Returns:
        Dictionary containing replenishment information
    """
    print(f"[TOOL] get_replenishment_info - Ejecutando con product_id={product_id}")
    try:
        replenishments = await odoo_manager.get_replenishment_info(product_id)
        return json.dumps({
            "replenishment_info": replenishments or [],
            "count": len(replenishments) if replenishments else 0,
            "success": True,
        })
    except Exception as e:
        print(f"Error getting replenishment info: {e}")
        return json.dumps({"success": False, "error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
