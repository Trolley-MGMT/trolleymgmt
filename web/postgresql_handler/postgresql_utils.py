import logging
from datetime import datetime

import psycopg

from web.variables.variables import AZ, AWS, GCP

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler('trolley_server.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Postgresql:
    def __init__(self, postgres_user: str = "", postgres_password: str = "",
                 postgres_host: str = "localhost", postgres_port: int = 5444,
                 postgres_dbname='cloud_pricing', provider_name: str = AZ, region_name: str = 'eastus'):
        self.postgres_dbname = postgres_dbname
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.provider_name = provider_name
        self.region_name = region_name

    def fetch_kubernetes_pricing(self) -> float:
        try:
            conn = psycopg.connect(
                dbname=self.postgres_dbname,
                user=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port
            )
            if self.provider_name == AZ:
                service_name = 'Azure Kubernetes Service'
            elif self.provider_name == AWS:
                service_name = 'AmazonEKS'
            elif self.provider_name == GCP:
                service_name = 'Kubernetes Engine'
            else:
                service_name = 'Azure Kubernetes Service'

            cursor = conn.cursor()
            sql_query = f"""
                SELECT prices, region
                FROM products
                WHERE "service" = '{service_name}' 
                  AND "region" = '{self.region_name}';
            """
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            cursor.close()
            conn.close()
            prices_dict = {}
            for row in rows:
                prices_desc, region = row
                values = prices_desc.values()
                effective_date_start = list(values)[0][0]['effectiveDateStart']
                if self.provider_name == AWS:
                    description = list(values)[0][0]['description']
                    if not 'Amazon EKS cluster usage' in description:
                        epoch_time = 0
                        prices_dict[epoch_time] = 0
                    else:
                        usd_price = list(values)[0][0]['USD']
                        timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%SZ')
                        epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                        prices_dict[epoch_time] = usd_price
                elif self.provider_name == AZ:
                    usd_price = list(values)[0][0]['USD']
                    timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%SZ')
                    epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                    prices_dict[epoch_time] = usd_price
                elif self.provider_name == GCP:
                    purchase_option = list(values)[0][0]['purchaseOption']
                    if purchase_option == 'OnDemand':
                        usd_price = list(values)[0][0]['USD']
                        timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%S.%fZ')
                        epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                        prices_dict[epoch_time] = usd_price
                    else:
                        epoch_time = 0
                        prices_dict[epoch_time] = 0

            data_float_values = {key: float(value) for key, value in prices_dict.items()}
            highest_value_key = max(data_float_values, key=data_float_values.get)
            latest_price = prices_dict[highest_value_key]
            return float(latest_price)

        except (Exception, psycopg.Error) as error:
            logger.error("Error while connecting to PostgreSQL:", error)
