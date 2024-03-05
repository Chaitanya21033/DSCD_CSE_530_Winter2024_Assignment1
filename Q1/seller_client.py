import time
import threading
import grpc
import uuid
import marketplace_pb2
import marketplace_pb2_grpc

# Configuration
SERVER_ADDRESS = "10.190.0.2:50051"
SELLER_ADDRESS = "10.190.0.3"

class SellerClient:
    def __init__(self, address):
        '''
        Client for the seller to interact with the marketplace.
        '''
        self.channel = grpc.insecure_channel(address)
        self.stub = marketplace_pb2_grpc.MarketplaceStub(self.channel)
        self.uuid = str(uuid.uuid4()).split('-')[0]
        self.seller_address = f"{SELLER_ADDRESS}:{self.uuid[:8]}"  # Mock IP:Port with UUID

    def register_seller(self):
        """Register the seller with the market."""
        try:
            response = self.stub.RegisterSeller(marketplace_pb2.RegisterSellerRequest(ip_port=self.seller_address, uuid=self.uuid))
            print(f"RegisterSeller response: {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"RegisterSeller failed with {e.code()}: {e.details()}")

    def add_item(self, name, category, quantity, description, price):
        """Add an item to the market."""
        item = marketplace_pb2.Item(
            name=name,
            category=category,
            quantity=quantity,
            description=description,
            seller_address=self.seller_address,
            price=price,
            rating=0.0  # Initial rating
        )
        try:
            response = self.stub.AddItem(marketplace_pb2.ItemOperationRequest(uuid=self.uuid, item=item))
            print(f"AddItem response: {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"AddItem failed with {e.code()}: {e.details()}")

    def update_item(self, item_id, quantity, price):
        """Update details of an existing item."""
        try:
            response = self.stub.UpdateItem(marketplace_pb2.UpdateItemRequest(uuid=self.uuid, id=item_id, quantity=quantity, price=price))
            print(f"UpdateItem response: {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"UpdateItem failed with {e.code()}: {e.details()}")

    def delete_item(self, item_id):
        """Delete an item from the market."""
        try:
            response = self.stub.DeleteItem(marketplace_pb2.DeleteItemRequest(uuid=self.uuid, id=item_id))
            print(f"DeleteItem response: {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"DeleteItem failed with {e.code()}: {e.details()}")

    def display_seller_items(self):
        """Display all items listed by the seller."""
        try:
            response = self.stub.DisplaySellerItems(marketplace_pb2.DisplaySellerItemsRequest(uuid=self.uuid))
            for item in response.items:
                rating = item.rating if item.rating != -1 else "UNRATED";
                print(f"Item ID: {item.id}, Name: {item.name}, Price: ${item.price}, Rating: {rating}, Quantity: {item.quantity}")
            return True
        except grpc.RpcError as e:
            print(f"DisplaySellerItems failed with {e.code()}: {e.details()}")
            return False
        
    def fetch_notifications(self):
        """Fetch and display notifications for the seller."""
        try:
            response = self.stub.FetchSellerNotifications(marketplace_pb2.NotificationRequest(uuid=self.uuid))
            for notification in response.messages:
                print(notification)
        except grpc.RpcError as e:
            print(f"Failed to fetch notifications: {e.code()}: {e.details()}")

    def start_notification_listener(self):
        """Start a background thread to listen for notifications."""
        
        def listener():
            while True:
                self.fetch_notifications()
                time.sleep(5)  # Adjust frequency as needed

        thread = threading.Thread(target=listener)
        thread.daemon = True
        thread.start()

def seller_menu(client):
    '''
    Seller menu for interacting with the marketplace.
    '''
    while True:
        print("\n===== Seller Menu =====")
        print("1. Register Seller")
        print("2. Add Item")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Display All Items")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            client.register_seller()
        elif choice == "2":
            name = input("Enter item name: ")
            category = input("Enter item category (ELECTRONICS, FASHION, OTHERS): ")
            category = "OTHERS" if category not in ["ELECTRONICS", "FASHION", "OTHERS"] else category #Error handling
            quantity = int(input("Enter quantity: "))
            description = input("Enter description: ")
            price = float(input("Enter price per unit: "))
            client.add_item(name, marketplace_pb2.Category.Value(category), quantity, description, price)
        elif choice == "3":
            item_id = int(input("Enter item ID to update: "))
            quantity = int(input("Enter new quantity: "))
            price = float(input("Enter new price: "))
            client.update_item(item_id, quantity, price)
        elif choice == "4":
            item_id = int(input("Enter item ID to delete: "))
            client.delete_item(item_id)
        elif choice == "5":
            client.display_seller_items()
        elif choice == "6":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    '''
    Start the seller client.
    '''
    client = SellerClient(SERVER_ADDRESS)
    if client.register_seller():
        client.start_notification_listener()
        seller_menu(client)


if __name__ == "__main__":
    main()