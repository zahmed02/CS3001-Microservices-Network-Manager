import grpc
import user_pb2
import user_pb2_grpc

def test_grpc():
    try:
        print("Testing gRPC connection...")
        channel = grpc.insecure_channel('localhost:50051')
        stub = user_pb2_grpc.UserServiceStub(channel)
        response = stub.GetUser(user_pb2.UserRequest(id="123"))
        print(f"✅ gRPC Response: {response}")
        return True
    except Exception as e:
        print(f"❌ gRPC Error: {e}")
        return False

if __name__ == "__main__":
    test_grpc()