from pydantic import BaseModel
from .client import ShopifyClient

class Query:
    return_type: BaseModel = None

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
    
    @property
    def fields(self):
        return ", ".join(self.return_type.model_fields.keys())
    
    def execute(self, client: ShopifyClient):
        variables = {
            name: getattr(self, name).to_graphql()
            for name in self.__dict__.keys()
        }
        response = client.request(
            query=self.body,
            variables=variables
        )
        print(response.extensions)
        try:
            order_data = response.data.get(self.class_name)
            cast_obj = self.return_type(**order_data)
        except Exception as e:
            raise e
        return cast_obj
