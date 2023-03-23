from grafanalib.core import (
    Dashboard, Graph,
    OPS_FORMAT, Row,
    single_y_axis, Target, TimeRange, YAxes, YAxis
)
from Dashboards.models.A11yDashboard import A11yDashboard


def build_dashboard(dash: A11yDashboard):
    dashboard = Dashboard(
        title=dash.title,
        rows=[
            Row(panels=[
                Graph(
                    title="Prometheus http requests",
                    dataSource='default',
                    targets=[
                        Target(
                            expr='rate(prometheus_http_requests_total[5m])',
                            legendFormat="{{ handler }}",
                            refId='A',
                        ),
                    ],
                    yAxes=single_y_axis(format=OPS_FORMAT),
                ),
            ]),
        ],
    ).auto_panel_ids()
    return dashboard
