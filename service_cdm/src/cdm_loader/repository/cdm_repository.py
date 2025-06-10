from lib.pg import PgConnect
from cdm_loader.repository.cdm_model import ProductCountersDTO


class CMDRepository:
    def __init__(self, db: PgConnect) -> None:
        self._db = db

    def user_product_counters_insert(self, product: ProductCountersDTO) -> None:
        with self._db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                        INSERT INTO cdm.user_product_counters (
                            user_id, 
                            product_id, 
                            product_name, 
                            order_cnt
                        )
                        VALUES (
                            %(user_id)s, 
                            %(product_id)s, 
                            %(product_name)s, 
                            %(order_cnt)s
                        )
                        ON CONFLICT(user_id, product_id) DO UPDATE 
                        SET product_name = EXCLUDED.product_name,
                            order_cnt = EXCLUDED.order_cnt;
                    """,
                    {
                        'user_id': product.user_id,
                        'product_id': product.product_id,
                        'product_name': product.product_name,
                        'order_cnt': product.order_cnt
                    }
                )

    def user_category_counters_insert(self, user_id: str) -> None:
        with self._db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                        INSERT INTO cdm.user_category_counters (
                            user_id, 
                            category_id, 
                            category_name, 
                            order_cnt
                        )
                        SELECT 
                            user_id, 
                            hc.h_category_pk AS category_id, 
                            category_name, 
                            SUM(order_cnt) AS order_cnt
                        FROM cdm.user_product_counters upc 
                        INNER JOIN dds.l_product_category lpc 
                          ON upc.product_id = lpc.h_product_pk 
                        INNER JOIN dds.h_category hc 
                          ON hc.h_category_pk = lpc.h_category_pk
                        WHERE user_id = %(user_id)s
                        GROUP BY user_id, hc.h_category_pk, category_name                        
                        ON CONFLICT(user_id, category_id) DO UPDATE
                        SET category_name = EXCLUDED.category_name,
                            order_cnt = EXCLUDED.order_cnt;
                    """,
                    {
                        'user_id': user_id
                    }
                )
