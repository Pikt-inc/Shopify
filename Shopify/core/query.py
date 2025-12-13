from pydantic import BaseModel
from .client import ShopifyClient
from typing import Optional, Dict, Any, Type

class Query:
    return_type: Optional[Type[BaseModel]] = None

    def __init__(
        self
    ):
        pass

    @property
    def class_name(self):
        return self.__class__.__name__ 

    @property
    def arguments(self):
        return ", ".join(
            f"${name}: {type(getattr(self, name)).__name__}!"
            for name in self.__dict__.keys()
        )
    
    @property
    def fields(self):
        if self.return_type is None:
            raise ValueError("return_type must be defined to access fields.")
        return ", ".join(self.return_type.model_fields.keys()) 

    @property
    def body(self) -> str:
        return f'''
        query {self.class_name}({self.arguments}) {{
            {self.class_name}({', '.join(f'{name}: ${name}' for name in self.__dict__.keys())}) {{
                {self.fields}
            }}
        }}
        '''
    
    def execute(self, client: ShopifyClient):
        variables = {
            name: getattr(self, name).to_graphql()
            for name in self.__dict__.keys()
        }
        response = client.request(
            query=self.body,
            variables=variables
        )
        print("DEBUG: Full Response:", response)
        if response.data is None:
            raise ValueError("Response data is None.")
        order_data = response.data.get(self.class_name)
        if not isinstance(order_data, dict):
            raise TypeError("Response data for the class must be a dictionary.")
        if self.return_type is None:
            raise ValueError("return_type must be defined to cast the response.")
        if not isinstance(self.return_type, type):
            raise TypeError("return_type must be a class type derived from BaseModel.")
        cast_obj = self.return_type(**order_data)
        return cast_obj
