from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from src.adapters.exceptions import AdapterException
from src.application.ports.secondary.bigquery_source_port import BigQuerySourcePort

if TYPE_CHECKING:
    from src.application.values.source_connector import SourceConnector


class BigQuerySourceAdapter(BigQuerySourcePort):
    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path

    def _get_client(self, connector: "SourceConnector"):  # type: ignore[return]
        try:
            from google.cloud import bigquery

            cred_path = connector.credentials_path or self._credentials_path
            if cred_path:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(cred_path)
                return bigquery.Client(
                    project=connector.gcp_project_id, credentials=credentials
                )
            return bigquery.Client(project=connector.gcp_project_id)
        except Exception as exc:
            raise AdapterException(f"Failed to initialise BigQuery client: {exc}") from exc

    def read_rows(
        self, connector: "SourceConnector", start_index: int = 0
    ) -> Iterator[dict]:
        try:
            client = self._get_client(connector)
            table_ref = f"{connector.gcp_project_id}.{connector.dataset_id}.{connector.table_id}"
            rows_iter = client.list_rows(
                table_ref,
                start_index=start_index,
                page_size=connector.page_size,
            )
            for page in rows_iter.pages:
                for row in page:
                    yield dict(row)
        except AdapterException:
            raise
        except Exception as exc:
            raise AdapterException(f"BigQuery read failed: {exc}") from exc

    def get_schema(self, connector: "SourceConnector") -> list[str]:
        try:
            client = self._get_client(connector)
            table_ref = f"{connector.gcp_project_id}.{connector.dataset_id}.{connector.table_id}"
            table = client.get_table(table_ref)
            return [field.name for field in table.schema]
        except AdapterException:
            raise
        except Exception as exc:
            raise AdapterException(f"BigQuery get_schema failed: {exc}") from exc
