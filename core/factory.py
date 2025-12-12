from .mutation import ShopifyMutationManager

class ResourceFactory(ShopifyMutationManager):
    _RESOURCE_TYPE = None

    def __init__(self, client, **kwargs):
        if not self._RESOURCE_TYPE:
            raise ValueError("RESOURCE_TYPE must be defined in the subclass.")
        
        super().__init__(client, **kwargs)

    def create(self, data: dict):
        try:
            resource = self._RESOURCE_TYPE(**data)
        except Exception as e:
            raise ValueError(f"Error creating resource: {e}")
        
        return resource
    
    def retrieve(self, identifier: str):
        resp = self.execute_mutation(
            mutation_type=self.MutationType.RETRIEVE,
            variables={"id": identifier}
        )
        print(resp)