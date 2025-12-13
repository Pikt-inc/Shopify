"""
mutation fulfillmentCreateV2($fulfillment: FulfillmentV2Input!, $message: String) {
  fulfillmentCreateV2(fulfillment: $fulfillment, message: $message) {
    fulfillment {
      # Fulfillment fields
    }
    userErrors {
      field
      message
    }
  }
}
"""
from .types import String, FulfillmentV2Input
class Mutation:
    pass

class fulfillmentCreateV2:

    def __init__(
        self,
        fulfillment: FulfillmentV2Input,
        message: String = None,
    ):
        self.fulfillment: FulfillmentV2Input = fulfillment
        self.message: String = message

    @property
    def class_name(self):
        return self.__class__.__name__
    
    @property
    def arguments(self):
        inputs = self.__dict__
        return ", ".join(
            f"${name}: {type(value).__name__}!"
            for name, value in inputs.items()
            if value is not None
        )
