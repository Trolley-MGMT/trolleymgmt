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
                 postgres_host: str = "localhost", postgres_port: int = 5432,
                 postgres_dbname='cloud_pricing', provider_name: str = AZ, region_name: str = '',
                 machine_type: str = ''):
        self.postgres_dbname = postgres_dbname
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.provider_name = provider_name
        self.region_name = region_name
        self.machine_type = machine_type

        try:
            self.conn = psycopg.connect(
                dbname=self.postgres_dbname,
                user=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port
            )

        except (Exception, psycopg.Error) as error:
            logger.error("Error while connecting to PostgreSQL:", error)

    def fetch_kubernetes_pricing(self) -> float:
        try:
            if self.provider_name == AZ:
                service_name = 'Azure Kubernetes Service'
            elif self.provider_name == AWS:
                service_name = 'AmazonEKS'
            elif self.provider_name == GCP:
                service_name = 'Kubernetes Engine'
            else:
                service_name = 'Azure Kubernetes Service'

            cursor = self.conn.cursor()
            sql_query = f"""
                SELECT prices, region
                FROM products
                WHERE "service" = '{service_name}' 
                  AND "region" = '{self.region_name}';
            """
            logger.info(
                f'Running the {sql_query} query with {self.postgres_dbname} {self.postgres_user} {self.postgres_password} {self.postgres_host}')
            cursor.execute(sql_query)
            rows = cursor.fetchall()

            cursor.close()
            self.conn.close()
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

    def fetch_vm_pricing(self) -> float:
        # That thing is no good
        if self.provider_name == AZ:
            service_name = 'Virtual Machines'
            product_family = 'Compute'
        elif self.provider_name == AWS:
            service_name = 'AmazonEC2'
            product_family = 'Compute Instance'
        elif self.provider_name == GCP:
            service_name = 'Compute Engine'
            product_family = 'Compute Instance'
        else:
            service_name = 'Azure Kubernetes Service'
            product_family = 'Compute Instance'
        cursor = self.conn.cursor()
        sql_query = f"""
            SELECT prices
	        FROM products
	        where "vendorName" = '{self.provider_name}' 
	        and "service" = '{service_name}' 
	        and "region" = '{self.region_name}' 
	        and "productFamily" = '{product_family}'
	        and "attributes"->>'instanceType' = '{self.machine_type}'
	        and "attributes"->>'tenancy' = 'Shared'
	        and "attributes"->>'operatingSystem' = 'Linux'
	        and "attributes"->>'preInstalledSw' = 'NA'
	        and "attributes"->>'capacitystatus' = 'Used';
        """

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        cursor.close()
        self.conn.close()
        prices_dict = {}
        try:
            if not len(rows[0][0]) > 0:
                return 0
        except Exception as e:
            logger.warning(
                f'The query for {self.machine_type} machine type in {self.region_name} region for '
                f'{self.provider_name} provider failed with: {e}')
        else:
            for row in rows:
                try:
                    effective_date_start = list(row[0].values())[0][0]['effectiveDateStart']
                    if self.provider_name == AWS:
                        for pricing_option in list(row[0].values()):
                            if not pricing_option[0]['purchaseOption'] == 'on_demand':
                                epoch_time = 0
                                prices_dict[epoch_time] = 0
                            else:
                                usd_price = pricing_option[0]['USD']
                                timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%SZ')
                                epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                                prices_dict[epoch_time] = usd_price
                    elif self.provider_name == AZ:
                        usd_price = list(row)[0][0]['USD']
                        timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%SZ')
                        epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                        prices_dict[epoch_time] = usd_price
                    elif self.provider_name == GCP:
                        purchase_option = list(row[0].values())[0][0]['purchaseOption']
                        if purchase_option == 'on_demand':
                            usd_price = list(row[0].values())[0][0]['USD']
                            timestamp_obj = datetime.strptime(effective_date_start, '%Y-%m-%dT%H:%M:%S.%fZ')
                            epoch_time = (timestamp_obj - datetime(1970, 1, 1)).total_seconds()
                            prices_dict[epoch_time] = usd_price
                        else:
                            epoch_time = 0
                            prices_dict[epoch_time] = 0
                except Exception as e:
                    logger.error(f'There was some problem parsing the query: {e}')

            try:
                data_float_values = {key: float(value) for key, value in prices_dict.items()}
                highest_value_key = max(data_float_values, key=data_float_values.get)
                latest_price = prices_dict[highest_value_key]
            except Exception as e:
                logger.error(f'Something went wrong {e}')
                latest_price = 0
            return float(latest_price)
