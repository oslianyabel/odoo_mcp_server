import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import aiofiles
import aiohttp
from aiohttp import BasicAuth

from config import config

# Configure logger
logger = logging.getLogger(__name__)


class OdooHttpException(Exception):
    pass


class OdooClient:
    def __init__(
        self,
        ODOO_URL,
        CLIENT_ID,
        CLIENT_SECRET,
        SEARCH_PATH,
        CREATE_PATH,
        TOKEN_PATH,
    ):
        self.__ODOO_URL = ODOO_URL
        self.__CLIENT_ID = CLIENT_ID
        self.__CLIENT_SECRET = CLIENT_SECRET
        self.__SEARCH_PATH = SEARCH_PATH
        self.__CREATE_PATH = CREATE_PATH
        self.__TOKEN_PATH = TOKEN_PATH

        self.__SEARCH_URL = f"{self.__ODOO_URL}{self.__SEARCH_PATH}"
        self.__CREATE_URL = f"{self.__ODOO_URL}{self.__CREATE_PATH}"
        self.__TOKEN_URL = f"{self.__ODOO_URL}{self.__TOKEN_PATH}"

        # Token management
        self.__access_token: Optional[str] = None
        self.__token_expires_at: Optional[datetime] = None
        self.__token_buffer_seconds = 300  # Renovar token 5 minutos antes de expirar

    async def http_get(self, url, headers, params):
        msg = f"URL: {url}\n"
        msg += f"headers: {headers}\n"
        msg += f"params: {params}\n"
        logger.debug(f"Get http request\n{msg}")
        async with aiohttp.ClientSession() as session:
            args = {"url": url, "headers": headers, "params": params}

            async with session.get(**args) as response:
                if response.ok:
                    return await response.json()
                else:
                    # Await the response body so logs/exceptions contain the real error text
                    body = await response.text()
                    logger.error(f"Odoo HTTP GET error {response.status}: {body}")
                    raise OdooHttpException(f"{response.status}: {body}")

    async def http_post_json(self, url, headers, json):
        msg = f"URL: {url}\n"
        msg += f"headers: {headers}\n"
        msg += f"json: {json}\n"
        logger.debug(f"Post http request\n{msg}")
        async with aiohttp.ClientSession() as session:
            args = {"url": url, "headers": headers, "json": json}

            async with session.post(**args) as response:
                logger.debug(f"Response status: {response.status}")
                if response.ok:
                    return await response.json()
                else:
                    body = await response.text()
                    logger.error(f"Odoo HTTP POST JSON error {response.status}: {body}")
                    raise OdooHttpException(f"{response.status}: {body}")

    async def http_post_data(self, url, headers, data):
        msg = f"URL: {url}\n"
        msg += f"headers: {headers}\n"
        msg += f"data: {data}\n"
        logger.debug(f"Post http request\n{msg}")
        async with aiohttp.ClientSession() as session:
            args = {"url": url, "headers": headers, "data": data}

            async with session.post(**args) as response:
                logger.debug(f"status code: {response.status}")
                if response.ok:
                    return await response.json()
                else:
                    body = await response.text()
                    logger.error(f"Odoo HTTP POST DATA error {response.status}: {body}")
                    raise OdooHttpException(f"{response.status}: {body}")

    async def http_post_auth(self, url, data, auth):
        """Authenticate and get OAuth token from Odoo API.

        Args:
            url: Token endpoint URL
            data: Authentication data
            auth: Basic auth credentials

        Returns:
            str: Access token

        Raises:
            Exception: If authentication fails
        """
        async with aiohttp.ClientSession() as session:
            args = {"url": url, "data": data, "auth": auth}

            async with session.post(**args) as response:
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

                    # Store token and calculate expiration time
                    self.__access_token = access_token
                    self.__token_expires_at = datetime.now() + timedelta(
                        seconds=expires_in
                    )

                    logger.info(
                        f"Token obtenido exitosamente. Expira en: {self.__token_expires_at}"
                    )
                    return access_token
                else:
                    error_text = await response.text()
                    raise Exception(f"Error al obtener el token Odoo: {error_text}")

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire.

        Returns:
            bool: True if token is expired or will expire soon
        """
        if not self.__access_token or not self.__token_expires_at:
            return True

        # Consider token expired if it expires within the buffer time
        buffer_time = datetime.now() + timedelta(seconds=self.__token_buffer_seconds)
        return self.__token_expires_at <= buffer_time

    async def _ensure_valid_token(self) -> str:
        """Ensure we have a valid, non-expired token.

        Returns:
            str: Valid access token

        Raises:
            Exception: If unable to obtain a valid token
        """
        if self._is_token_expired():
            logger.info("Token expirado o próximo a expirar, renovando...")
            await self.get_oauth_token()

        if not self.__access_token:
            raise Exception("No se pudo obtener un token válido")

        return self.__access_token

    async def get_oauth_token(self) -> str:
        """Get a new OAuth token from Odoo API.

        Returns:
            str: Access token
        """
        logger.info("Obteniendo nuevo token de Odoo...")
        data = {"grant_type": "client_credentials"}
        auth = BasicAuth(self.__CLIENT_ID, self.__CLIENT_SECRET)
        return await self.http_post_auth(self.__TOKEN_URL, data, auth)

    async def _make_authenticated_request(self, request_func, *args, **kwargs):
        """Make an authenticated request with automatic token renewal on 401 errors.

        Args:
            request_func: The function to call (http_get, http_post_data, etc.)
            *args: Arguments to pass to the request function
            **kwargs: Keyword arguments to pass to the request function

        Returns:
            Response from the API

        Raises:
            Exception: If request fails after token renewal attempt
        """
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Ensure we have a valid token
                token = await self._ensure_valid_token()

                # Update headers with current token if they exist in kwargs
                if "headers" in kwargs:
                    kwargs["headers"]["Authorization"] = f"Bearer {token}"
                elif len(args) > 1:  # For positional arguments
                    # This handles cases where headers is the second argument
                    args = list(args)
                    if isinstance(args[1], dict):
                        args[1]["Authorization"] = f"Bearer {token}"
                    args = tuple(args)

                return await request_func(*args, **kwargs)

            except Exception as e:
                error_msg = str(e).lower()

                # Check if it's an authentication error
                if (
                    "401" in error_msg
                    or "unauthorized" in error_msg
                    or "invalid_token" in error_msg
                    or "token_expired" in error_msg
                ):
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Token inválido detectado, renovando... (intento {attempt + 1})"
                        )
                        # Force token renewal
                        self.__access_token = None
                        self.__token_expires_at = None
                        continue
                    else:
                        logger.error(
                            "Falló la renovación del token después de múltiples intentos"
                        )
                        raise Exception(f"Error de autenticación persistente: {e}")
                else:
                    # Not an auth error, re-raise immediately
                    raise e

        raise Exception("Se agotaron los intentos de autenticación")

    async def create_odoo(self, model, args):
        """Create a record in Odoo with automatic token management.

        Args:
            model: Odoo model name
            args: Arguments for record creation

        Returns:
            Created record data
        """
        headers = {
            "Authorization": "Bearer placeholder"
        }  # Will be updated by _make_authenticated_request
        data = {
            "model": model,
            "method": "create",
            "args": args,
        }

        return await self._make_authenticated_request(
            self.http_post_data, self.__CREATE_URL, headers, data
        )

    async def fetch_odoo(
        self,
        model,
        fields,
        domain,
        order=None,
        limit=None,
        group_by=None,
        cookie=None,
    ):
        """Fetch records from Odoo with automatic token management.

        Args:
            model: Odoo model name
            fields: Fields to retrieve
            domain: Search domain
            order: Sort order
            limit: Maximum number of records
            group_by: Group by field
            cookie: Optional cookie for session

        Returns:
            List of records from Odoo
        """
        headers = {
            "Authorization": "Bearer placeholder",  # Will be updated by _make_authenticated_request
        }
        if cookie:
            headers["Cookie"] = cookie

        params = {
            "model": model,
            "fields": fields,
            "domain": domain,
        }
        if order:
            params["order"] = order
        if limit:
            params["limit"] = limit
        if group_by:
            params["group_by"] = group_by

        return await self._make_authenticated_request(
            self.http_get, self.__SEARCH_URL, headers, params
        )

    async def get_report(
        self,
        sale_order_id,
        raw=None,
        cookie=None,
    ):
        headers = {
            "Authorization": f"Bearer {self.__access_token}",
        }
        if cookie:
            headers["Cookie"] = cookie

        if raw:
            endpoint = f"/api/v2/report/sale.report_saleorder_raw?ids=%5B{sale_order_id}%5D&type=PDF"
        else:
            endpoint = f"/api/v2/report/sale.report_saleorder?ids=%5B{sale_order_id}%5D&type=PDF"

        url = config.ODOO_URL + endpoint  # type: ignore

        report = await self._make_authenticated_request(self.http_get, url, headers, {})

        report_binary = base64.b64decode(report["content"])
        path = f"static/reports/{sale_order_id}.pdf"
        async with aiofiles.open(path, "wb") as f:
            await f.write(report_binary)

        return path


class OdooManager(OdooClient):
    def __init__(self, product_fields=None):
        if product_fields:
            self.product_fields = product_fields
        else:
            self.product_fields = json.dumps(
                [
                    "id",
                    "name",
                    "default_code",
                    "x_studio_marca",
                    "barcode",
                    "categ_id",
                    "qty_available",
                    "list_price",
                    "currency_id",
                    "tax_string",
                    "description_sale",
                    "invoice_policy",
                    "taxes_id",
                    "active",
                    "type",
                ]
            )
        super().__init__(
            ODOO_URL=config.ODOO_URL,
            CLIENT_ID=config.ODOO_CLIENT_ID,
            CLIENT_SECRET=config.ODOO_CLIENT_SECRET,
            SEARCH_PATH=config.SEARCH_PATH,
            CREATE_PATH=config.CREATE_PATH,
            TOKEN_PATH=config.TOKEN_PATH,
        )

    async def get_partner(self, phone=False, email=False, id=False) -> dict | None:
        fields = json.dumps(
            [
                "id",
                "name",
                "company_type",
                "parent_id",
                "phone",
                "email",
                "website",
                "mobile",
                "street",
                "city",
                "street2",
                "zip",
                "country_id",
                "state_id",
                "vat",
                "company_id",
                "customer_rank",
                "supplier_rank",
                "credit",
                "debit",
                "category_id",
                "lang",
                "industry_id",
                "type",
                "is_company",
            ]
        )
        domain = json.dumps(
            [["name", "!=", ""], ["email", "!=", ""], ["phone", "!=", ""]]
        )
        if phone:
            domain = json.dumps([["phone", "=", phone]])
        elif email:
            domain = json.dumps([["email", "=", email]])
        elif id:
            domain = json.dumps([["id", "=", id]])

        partners = await self.fetch_odoo("res.partner", fields, domain, limit=1)
        if partners:
            return partners[0]

        logger.warning(f"No se encontró ningún partner con el teléfono {phone}")
        return None

    async def get_partner_by_id(self, id):
        logger.debug(f"get_partner_by_id {id}")
        return await self.get_partner(id=id)

    async def get_partner_by_phone(self, phone):
        logger.debug(f"get_partner_by_phone {phone}")
        return await self.get_partner(phone=phone)

    async def get_partner_by_email(self, email):
        logger.debug(f"get_partner_by_email {email}")
        return await self.get_partner(email=email)

    async def get_product(
        self, id=None, sku=None, name=None, template_first=True
    ) -> dict | None:
        fields = self.product_fields
        domain = json.dumps([["active", "=", True]])

        if sku:
            domain = json.dumps([["default_code", "=", sku]])

        elif name:
            name = name.replace(" ", "%")
            name = f"%{name}%"
            domain = json.dumps([["name", "ilike", name]])

        elif id:
            domain = json.dumps([["id", "=", id]])

        if template_first:
            models = ["product.template", "product.product"]
        else:
            models = ["product.product", "product.template"]

        for m in models:
            product_data = await self.fetch_odoo(m, fields, domain)
            if product_data:
                return product_data[0]

        return None

    async def download_image(self, image_base64, sku):
        if not image_base64:
            logger.warning(f"La imagen del producto con sku {sku} no existe")
            return

        logger.info(f"Descargando imagen del producto con sku {sku}...")
        image_binary = base64.b64decode(image_base64)
        path = f"static/images/{sku}.jpg"
        async with aiofiles.open(path, "wb") as f:
            await f.write(image_binary)

        logger.info(f"Imagen descargada y guardada en {path}")
        return path

    async def get_all_products(self) -> list[dict] | None:
        fields = json.dumps(
            [
                "id",
                "name",
                "default_code",
                "x_studio_marca",
                "barcode",
                "qty_available",
                "list_price",
            ]
        )
        domain = json.dumps(
            [["active", "=", True], ["qty_available", ">", 0], ["list_price", ">", 0]]
        )
        product_data, template_data = await asyncio.gather(
            self.fetch_odoo("product.product", fields, domain, order="id"),
            self.fetch_odoo("product.template", fields, domain, order="id"),
        )
        results = []
        default_code_list = []
        for p in product_data + template_data:
            if p["default_code"] not in default_code_list:
                results.append(p)
                default_code_list.append(p["default_code"])

        logger.info(f"Se encontraron {len(results)} productos")
        return results

    async def create_attachment(
        self, name: str, datas_b64: str, res_model: str, res_id: int
    ) -> dict:
        """Create an ir.attachment bound to a record.

        Args:
            name: Attachment filename
            datas_b64: Base64-encoded file bytes (without data URI prefix)
            res_model: Model name e.g. 'helpdesk.ticket'
            res_id: Record ID
        """
        args = json.dumps(
            [
                {
                    "name": name,
                    "datas": datas_b64,
                    "res_model": res_model,
                    "res_id": int(res_id),
                }
            ]
        )
        logger.info(
            f"Creating attachment name={name} model={res_model} res_id={res_id} size={len(datas_b64)}b64"
        )
        return await self.create_odoo("ir.attachment", args)

    async def get_product_by_sku(self, sku, template_first=True) -> dict | None:
        return await self.get_product(sku=sku, template_first=template_first)

    async def get_product_by_name(self, name) -> list[dict] | None:
        fields_json = self.product_fields
        # build ilike pattern
        q = name.replace(" ", "%")
        q = f"%{q}%"
        domain = json.dumps([["name", "ilike", q], ["active", "=", True]])

        results = []
        try:
            tmpl = await self.fetch_odoo("product.template", fields_json, domain)
            if tmpl:
                results += tmpl
        except OdooHttpException:
            pass

        try:
            prods = await self.fetch_odoo("product.product", fields_json, domain)
            if prods:
                results += prods
        except OdooHttpException:
            pass

        unique_products = []
        sku_list = []
        for p in results:
            if not p["barcode"] and not p["default_code"] or not p["x_studio_marca"]:
                continue

            if p["default_code"] not in sku_list:
                unique_products.append(p)
                sku_list.append(p["default_code"])

        return unique_products

    async def get_product_by_id(self, id, template_first=True) -> dict | None:
        return await self.get_product(id=id, template_first=template_first)

    async def get_sale_order(
        self, name=None, id=None, marketplace=None
    ) -> list[dict] | None:
        if name:
            domain = json.dumps(
                [
                    "|",
                    "|",
                    ["name", "ilike", name],
                    ["reference_request", "ilike", name],
                    ["origin", "ilike", name],
                ]
            )
        elif id:
            domain = json.dumps([["id", "=", id]])
        elif marketplace:
            domain = json.dumps([["biomag_marketplace", "ilike", marketplace]])
        else:
            domain = json.dumps([["amount_total", ">", 0]])

        fields = json.dumps(
            [
                "id",
                "name",
                "partner_id",
                "date_order",
                "order_line",
                "state",
                "amount_total",
                "user_id",
                "company_id",
                "access_token",
                "access_url",
                "biomag_marketplace",
                "reference_request",
                "origin",
                "activity_ids",
            ]
        )

        sale_orders = await self.fetch_odoo("sale.order", fields, domain)
        if sale_orders:
            logger.info(f"Se encontraron {len(sale_orders)} pedidos")
            results = []
            for sale_order in sale_orders:
                link = config.ODOO_URL + str(sale_order["access_url"])
                if sale_order["access_token"]:
                    link += "?access_token=" + str(sale_order["access_token"])

                sale_order["link"] = link
                results.append(sale_order)

            return results

        logger.warning(f"No se encontraron pedidos con nombre: {name}")
        return None

    async def get_sale_orders_by_marketplace(self, marketplace) -> list[dict] | None:
        return await self.get_sale_order(marketplace=marketplace)

    async def get_sale_order_by_name(self, name) -> list[dict] | None:
        return await self.get_sale_order(name=name)

    async def get_sale_order_by_id(self, id) -> list[dict] | None:
        return await self.get_sale_order(id=id)

    async def verify_order(self, order, partner_id):
        real_order = await self.get_sale_order_by_id(order["id"])
        # verifica que el pedido le pertenezca al partner
        if real_order and real_order["partner_id"][0] == partner_id:  # type: ignore
            return order

        logger.warning(
            f"No se pudo verificar que el pedido {order['name']} pertenece al usuario"
        )
        return None

    async def get_sale_orders_by_partner(self, partner_id) -> list[dict] | None:
        domain = json.dumps([["partner_id", "=", partner_id]])
        fields = json.dumps(
            [
                "id",
                "name",
                "partner_id",
                "date_order",
                "order_line",
                "state",
                "amount_total",
                "user_id",
                "company_id",
                "access_token",
                "access_url",
            ]
        )

        orders = await self.fetch_odoo("sale.order", fields, domain)
        for order in orders:
            link = config.ODOO_URL + str(order["access_url"])
            if order["access_token"]:
                link += "?access_token=" + str(order["access_token"])

            order["link"] = link

        return orders

        # problema raro pasado
        if orders:
            tasks = [self.verify_order(order, partner_id) for order in orders]
            results = await asyncio.gather(*tasks)
            verified_orders = [order for order in results if order is not None]
            return verified_orders

        return None

    async def create_lead(self, partner, resume, email) -> dict:
        args = json.dumps(
            [
                {
                    "stage_id": 1,
                    "type": "opportunity",
                    "name": f"WhatsApp - {partner['name']}",
                    "email_from": email,
                    "phone": partner["phone"],
                    "description": resume,
                    "partner_id": partner["id"],
                }
            ]
        )

        lead_info = await self.create_odoo("crm.lead", args)
        logger.info(f"Lead creado: {lead_info}")
        return lead_info

    async def create_partner(self, name, phone, email=None) -> tuple[dict | None, str]:
        partner = await self.get_partner_by_phone(phone)
        if partner:
            logger.info(f"Partner found: {partner}")
            return partner, "ALREADY"

        args = [{}]
        args[0]["name"] = name
        args[0]["phone"] = phone
        if email:
            args[0]["email"] = email

        await self.create_odoo("res.partner", json.dumps(args))
        partner = await self.get_partner_by_phone(phone)
        if partner:
            logger.info(f"Partner created: {partner}")
            return partner, "CREATE"

        logger.error(f"Error asignando teléfono {phone} al nuevo partner {name}")
        return None, "ERROR"

    async def create_sale_order(self, partner_id, order_line) -> int:
        logger.info("Creando pedido...")
        order_line_commands = [(0, 0, line) for line in order_line]
        args = json.dumps(
            [
                {
                    "partner_id": partner_id,
                    "order_line": order_line_commands,
                    "company_id": 1,
                    "access_token": str(uuid.uuid4()),
                }
            ]
        )

        sale_order = await self.create_odoo("sale.order", args)
        logger.info(f"Pedido creado: {sale_order}")
        return sale_order

    async def create_order_line(self, products):
        logger.info("Creating order lines...")
        order_line = []
        try:
            for p in products:
                odoo_product = await self.get_product_by_sku(p["default_code"])
                if not odoo_product:
                    logger.warning(f"Product with sku {p['default_code']} not exists")
                    continue
                if odoo_product["qty_available"] < 1:
                    logger.warning(
                        f"product {p['name']} with sku: {p['default_code']} out of stock"
                    )
                    continue

                order_line.append(
                    {
                        "product_id": odoo_product["id"],
                        "product_uom_qty": p["uom_qty"],
                        "price_unit": odoo_product["list_price"] * p["uom_qty"],
                    }
                )
                # end for
            logger.info(f"Order lines created: {order_line}")
            return order_line

        except Exception as exc:
            logger.error(f"Error creating order lines: {str(exc)}")
            return False

    async def get_children_ids(self, category_id):
        children_ids = [category_id]
        children = await self.get_categories_children(category_id)
        for child in children:
            children_ids.append(child["id"])
            if child["child_id"]:
                children += await self.get_categories_children(child["id"])

        logger.debug(f"category_id {category_id} tiene {len(children)} categorías hijas")
        return children_ids

    async def get_products_by_category_name(self, category_name):
        # return {'category_name': [products], ...}
        logger.debug(f"get_products_by_category_name({category_name})")

        category_id_list = await self.get_categories_by_name(category_name)
        ans = {}
        for category in category_id_list:
            products = await self.get_products_by_category_id(category["id"])
            ans[category["name"]] = products

        return ans

    async def get_products_by_category_id(self, category_id) -> list[dict]:
        logger.debug(f"get_products_by_category_id({category_id})")

        fields = self.product_fields
        category_id_list = await self.get_children_ids(category_id)
        tasks = []
        for id in category_id_list:
            domain = json.dumps([["categ_id", "=", id], ["active", "=", True]])
            tasks.append(self.fetch_odoo("product.product", fields, domain, limit=100))
        results = await asyncio.gather(*tasks)
        product_data = []
        for r in results:
            product_data += r

        if product_data:
            logger.info(f"{len(product_data)} productos encontrados")
            return product_data

        return []

    async def get_categories(
        self, id=None, name=None, parent_id=None, child_id=None
    ) -> list[dict]:
        if id:
            domain = json.dumps([["id", "=", id]])
        elif name:
            domain = json.dumps([["name", "ilike", name]])
        elif parent_id:
            domain = json.dumps([["parent_id", "=", parent_id]])
        elif child_id:
            domain = json.dumps([["child_id", "=", child_id]])
        else:
            domain = ""
        fields = json.dumps(["id", "name", "parent_id", "child_id", "product_count"])
        categories = await self.fetch_odoo("product.category", fields, domain)
        if categories:
            return categories

        return []

    async def get_category_by_id(self, id):
        logger.debug(f"get_category_by_id({id})")
        return await self.get_categories(id=id)

    async def get_categories_by_name(self, name):
        logger.debug(f"get_categories_by_name({name})")
        return await self.get_categories(name=name)

    async def get_categories_children(self, parent_id):
        logger.debug(f"get_categories_children({parent_id})")
        return await self.get_categories(parent_id=parent_id)

    async def get_category_parent(self, child_id):
        logger.debug(f"get_category_parent({child_id})")
        return await self.get_categories(child_id=child_id)

    async def get_all_categories(self):
        logger.debug("get_all_categories()")
        return await self.get_categories()

    async def get_images_by_product_id(self, product_id, product_sku) -> list[str]:
        domain = json.dumps([["product_tmpl_id", "=", product_id]])
        domain2 = json.dumps([["product_variant_id", "=", product_id]])

        fields = json.dumps(
            [
                "product_tmpl_id",
                "name",
                "product_variant_id",
                "image_1024",
            ]
        )

        try:
            images = await self.fetch_odoo("product.image", fields, domain)  # type: ignore
            if not images:
                images = await self.fetch_odoo("product.image", fields, domain2)  # type: ignore
                if not images:
                    return []
        except OdooHttpException as exc:
            # Si el modelo product.image no existe en esta DB, intentar fallback
            logger.warning(
                f"Error fetching product images from Odoo for product_id {product_id}: {exc}"
            )
            try:
                # Intentar recuperar image_1024 desde product.template
                simple_fields = json.dumps(["image_1024"])
                domain_id = json.dumps([["id", "=", product_id]])
                tpl = await self.fetch_odoo(
                    "product.template", simple_fields, domain_id, limit=1
                )  # type: ignore
                if tpl and tpl[0].get("image_1024"):
                    file_name = f"{product_sku}_0"
                    images_path = [file_name]
                    await self.download_image(tpl[0]["image_1024"], file_name)
                    return images_path

                prod = await self.fetch_odoo(
                    "product.product", simple_fields, domain_id, limit=1
                )  # type: ignore
                if prod and prod[0].get("image_1024"):
                    file_name = f"{product_sku}_0"
                    images_path = [file_name]
                    await self.download_image(prod[0]["image_1024"], file_name)
                    return images_path

            except Exception as exc2:
                logger.error(f"Fallback fetch failed for product_id {product_id}: {exc2}")

            return []

        images_path = []
        for idx, image in enumerate(images):
            file_name = f"{product_sku}_{idx}"  # type: ignore
            images_path.append(file_name)
            await self.download_image(image["image_1024"], file_name)  # type: ignore

        return images_path

    # ============================
    # Extra business endpoints
    # ============================

    async def get_pending_invoices(self, partner_id: int) -> list[dict] | None:
        fields = json.dumps(
            [
                "id",
                "name",
                "invoice_date",
                "invoice_date_due",
                "amount_total",
                "payment_state",
                "partner_id",
            ]
        )
        domain = json.dumps(
            [
                ["partner_id", "=", partner_id],
                ["move_type", "=", "out_invoice"],
                ["payment_state", "!=", "paid"],
            ]
        )
        invoices = await self.fetch_odoo(
            "account.move", fields, domain, order="invoice_date desc"
        )
        return invoices or None

    async def get_top_customers(
        self, date_from: str | None = None, date_to: str | None = None, limit: int = 10
    ) -> list[dict] | None:
        # Simplified: fetch sale orders and aggregate totals per partner
        fields = json.dumps(
            ["id", "name", "partner_id", "amount_total", "date_order", "state"]
        )
        domain = [["state", "in", ["sale", "done"]]]
        if date_from:
            domain.append(["date_order", ">=", date_from])
        if date_to:
            domain.append(["date_order", "<=", date_to])
        orders = await self.fetch_odoo(
            "sale.order",
            fields,
            json.dumps(domain),
            order="amount_total desc",
            limit=1000,
        )
        agg: dict[int, dict] = {}
        for o in orders or []:
            pid = o["partner_id"][0]
            pname = o["partner_id"][1]
            agg.setdefault(
                pid,
                {
                    "partner_id": pid,
                    "partner_name": pname,
                    "amount_total": 0.0,
                    "orders": 0,
                },
            )
            agg[pid]["amount_total"] += o["amount_total"]
            agg[pid]["orders"] += 1
        top = sorted(agg.values(), key=lambda x: x["amount_total"], reverse=True)[
            :limit
        ]
        return top or None

    async def get_top_selling_products(
        self, date_from: str | None = None, date_to: str | None = None, limit: int = 10
    ) -> list[dict] | None:
        # Fetch sale.order.line and aggregate quantities per product
        fields = json.dumps(
            ["product_id", "product_uom_qty", "price_total", "order_id", "create_date"]
        )
        domain = []
        if date_from:
            domain.append(["create_date", ">=", date_from])
        if date_to:
            domain.append(["create_date", "<=", date_to])
        lines = await self.fetch_odoo(
            "sale.order.line", fields, json.dumps(domain), limit=5000
        )
        agg: dict[int, dict] = {}
        for line in lines or []:
            pid = line["product_id"][0]
            pname = line["product_id"][1]
            agg.setdefault(
                pid,
                {"product_id": pid, "product_name": pname, "qty": 0.0, "revenue": 0.0},
            )
            agg[pid]["qty"] += line["product_uom_qty"]
            agg[pid]["revenue"] += line["price_total"]
        top = sorted(agg.values(), key=lambda x: x["qty"], reverse=True)[:limit]
        return top or None

    async def get_orders_by_date(
        self, date_from: str, date_to: str
    ) -> list[dict] | None:
        fields = json.dumps(
            ["id", "name", "partner_id", "date_order", "amount_total", "state"]
        )
        domain = json.dumps(
            [["date_order", ">=", date_from], ["date_order", "<=", date_to]]
        )
        orders = await self.fetch_odoo(
            "sale.order", fields, domain, order="date_order desc"
        )
        return orders or None

    async def get_helpdesk_tickets(self, partner_id: int) -> list[dict] | None:
        fields = json.dumps(
            [
                "id",
                "name",
                "create_date",
                "stage_id",
                "user_id",
                "partner_id",
                "description",
            ]
        )
        domain = json.dumps([["partner_id", "=", partner_id]])
        tickets = await self.fetch_odoo(
            "helpdesk.ticket", fields, domain, order="create_date desc"
        )
        return tickets or None

    async def create_helpdesk_ticket(
        self, partner_id: int, name: str, description: str | None = None
    ) -> dict:
        args = json.dumps(
            [
                {
                    "name": name,
                    "partner_id": partner_id,
                    **({"description": description} if description else {}),
                }
            ]
        )
        ticket = await self.create_odoo("helpdesk.ticket", args)
        return ticket

    async def create_sale_order_by_product_id(
        self, partner_id: int, product_id: int, quantity: int = 1
    ) -> dict:
        """Create a sale order with a single product by product ID."""
        logger.info(f"Creating sale order for partner {partner_id} with product {product_id}")

        # Get product details to validate it exists
        product = await self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        # Create order line
        order_line = [
            {
                "product_id": product_id,
                "product_uom_qty": quantity,
                "price_unit": product.get("list_price", 0.0),
            }
        ]

        # Create the sale order
        return await self.create_sale_order(partner_id, order_line)

    async def get_replenishment_info(
        self, product_id: int | None = None
    ) -> list[dict] | None:
        """Get replenishment/procurement information for products."""
        fields = json.dumps(
            [
                "id",
                "product_id",
                "product_qty",
                "product_uom_id",
                "date_planned",
                "origin",
                "state",
                "priority",
                "rule_id",
                "warehouse_id",
            ]
        )

        if product_id:
            domain = json.dumps([["product_id", "=", product_id]])
        else:
            # Get all active replenishment records
            domain = json.dumps([["state", "in", ["confirmed", "assigned", "waiting"]]])

        try:
            replenishments = await self.fetch_odoo(
                "stock.rule", fields, domain, order="date_planned asc", limit=100
            )
            return replenishments or None
        except OdooHttpException:
            # Fallback to procurement.group if stock.rule doesn't exist
            try:
                fallback_fields = json.dumps(
                    ["id", "name", "partner_id", "move_type", "state"]
                )
                fallback_domain = json.dumps([["state", "!=", "done"]])
                groups = await self.fetch_odoo(
                    "procurement.group", fallback_fields, fallback_domain, limit=50
                )
                return groups or None
            except OdooHttpException:
                logger.warning("No replenishment models available in this Odoo instance")
                return None


odoo_manager = OdooManager()

if __name__ == "__main__":

    async def main():
        logger.info(await odoo_manager.get_oauth_token())

    asyncio.run(main())
