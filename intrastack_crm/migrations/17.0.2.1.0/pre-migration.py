"""Repair legacy service-product XML IDs before loading version 17.0.2.1.0.

Earlier releases created the service records as ``product.template`` while
quotation template lines point to ``product.product``.  A normal XML upgrade
cannot change the model attached to an existing external ID, so rebind each
legacy ID to its single generated product variant before data files are loaded.
"""

PRODUCT_XMLIDS = (
    "product_staffing_resource",
    "product_staffing_senior",
    "product_staffing_lead",
    "product_consulting_discovery",
    "product_consulting_implementation",
    "product_consulting_project_mgmt",
    "product_managed_monthly",
    "product_managed_onboarding",
    "product_managed_addon_hours",
)


def migrate(cr, version):
    """Point legacy template XML IDs at their one product variant."""
    cr.execute(
        """
        SELECT imd.name, imd.res_id, COUNT(pp.id)
          FROM ir_model_data AS imd
     LEFT JOIN product_product AS pp
            ON pp.product_tmpl_id = imd.res_id
         WHERE imd.module = 'intrastack_crm'
           AND imd.name = ANY(%s)
           AND imd.model = 'product.template'
      GROUP BY imd.id, imd.name, imd.res_id
        HAVING COUNT(pp.id) <> 1
        """,
        (list(PRODUCT_XMLIDS),),
    )
    invalid = cr.fetchall()
    if invalid:
        details = ", ".join(
            "%s(template=%s, variants=%s)" % row for row in invalid
        )
        raise RuntimeError(
            "Cannot migrate IntraStack service-product external IDs: " + details
        )

    cr.execute(
        """
        WITH product_mapping AS (
            SELECT imd.id AS xmlid_id, MIN(pp.id) AS product_id
              FROM ir_model_data AS imd
              JOIN product_product AS pp
                ON pp.product_tmpl_id = imd.res_id
             WHERE imd.module = 'intrastack_crm'
               AND imd.name = ANY(%s)
               AND imd.model = 'product.template'
          GROUP BY imd.id
        )
        UPDATE ir_model_data AS imd
           SET model = 'product.product',
               res_id = product_mapping.product_id
          FROM product_mapping
         WHERE imd.id = product_mapping.xmlid_id
        """,
        (list(PRODUCT_XMLIDS),),
    )
