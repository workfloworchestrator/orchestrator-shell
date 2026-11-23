# Copyright 2026 SURF, GÉANT.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""In-memory orchestrator-core models for the shell tests.

The SQLAlchemy models are instantiated without a session: they are plain Python objects until they
are added to a database. Reading most attributes works, but lazy relationships (for example
``SubscriptionInstanceTable.depends_on``) inspect the session state, so tests replace those on the
instance with plain lists. That needs no database and no ``init_database``.
"""

from datetime import datetime

from orchestrator.core.db import (
    ProcessTable,
    ProductBlockTable,
    ResourceTypeTable,
    SubscriptionInstanceTable,
    SubscriptionInstanceValueTable,
    SubscriptionTable,
    WorkflowTable,
)


def process(
    process_id: str, workflow_name: str, started_at: datetime | None, last_status: str = "completed"
) -> ProcessTable:
    """Return a process; ``workflow_name`` lives on the related workflow row."""
    instance = ProcessTable(
        process_id=process_id,
        created_by="test",
        last_status=last_status,
        last_step=None,
        started_at=started_at,
        last_modified_at=started_at,
    )
    instance.workflow = WorkflowTable(name=workflow_name, target=f"{workflow_name.upper()}_TARGET", description="")
    return instance


def resource_type(name: str, resource_type_id: str | None = None) -> ResourceTypeTable:
    """Return a resource type definition."""
    return ResourceTypeTable(resource_type=name, resource_type_id=resource_type_id or f"rt-{name}")


def product_block(name: str, *resource_type_names: str) -> ProductBlockTable:
    """Return a product block that defines the given resource types."""
    return ProductBlockTable(name=name, resource_types=[resource_type(name) for name in resource_type_names])


def value(
    product_block_value: ResourceTypeTable, value_: str | None, value_id: str | None = None
) -> SubscriptionInstanceValueTable:
    """Return a set (``value`` not None) or unset resource type value of a product block."""
    return SubscriptionInstanceValueTable(
        resource_type_id=product_block_value.resource_type_id,
        resource_type=product_block_value,
        value=value_,
        subscription_instance_value_id=value_id or f"siv-{product_block_value.resource_type}",
    )


def subscription_instance(
    block: ProductBlockTable,
    instance_id: str,
    *values: SubscriptionInstanceValueTable,
    depends_on: tuple[SubscriptionInstanceTable, ...] = (),
    in_use_by: tuple[SubscriptionInstanceTable, ...] = (),
) -> SubscriptionInstanceTable:
    """Return a product block of a subscription with its set resource type values."""
    instance = SubscriptionInstanceTable(
        subscription_instance_id=instance_id,
        subscription_id=f"sub-{instance_id}",
        product_block_id=f"pb-{instance_id}",
        product_block=block,
        values=list(values),
        label=None,
    )
    # Relationships are session-backed; use plain lists so no database is involved.
    instance.depends_on = list(depends_on)
    instance.in_use_by = list(in_use_by)
    return instance


def subscription(
    subscription_id: str,
    description: str,
    *instances: SubscriptionInstanceTable,
    start_date: datetime | None = None,
) -> SubscriptionTable:
    """Return a subscription with its product blocks."""
    result = SubscriptionTable(
        subscription_id=subscription_id,
        description=description,
        status="active",
        product_id=f"product-{subscription_id}",
        customer_id=f"customer-{subscription_id}",
        insync=False,
        start_date=start_date,
        end_date=None,
        note=None,
        instances=list(instances),
    )
    for instance in instances:
        # The column keeps the denormalized foreign key; set it to the owning subscription.
        instance.subscription_id = subscription_id
    return result
