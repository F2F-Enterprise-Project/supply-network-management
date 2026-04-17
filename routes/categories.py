# routes/category.py
from lightapi import RestEndpoint, Field

class Category(RestEndpoint):
    category_id: str = Field(unique=True)
    parent_category_id: str = Field(foreign_key="categorys.category_id", nullable=True)
    category_name: str = Field(max_length=100)
    level: int = Field()

    class Meta:
        table_name = "categories"
        endpoint = "/api/v1/categories"