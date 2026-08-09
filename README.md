# FastAPI + FastMCP + Astro + MongoDB on Kubernetes (Minikube)

A small **Reminders App** built to practice Kubernetes locally with Minikube.

![Uploading image.png…]()


## Architecture

```text
Browser / MCP Client
        |
        v
   reminders.test
        |
        v
   NGINX Ingress
        |
        +--------------------+
        |                    |
        v                    v
Frontend Service        API Service
        |                    |
   +----+----+          +----+----+----+
   |         |          |         |    |
Astro-1   Astro-2    API-1     API-2 API-3
                              |
                              v
                     MongoDB Replica Set
                    +---------+---------+
                    |         |         |
                 mongo-0   mongo-1   mongo-2
                    |         |         |
                   PVC       PVC       PVC
```

The project uses:

- **Astro** frontend
- **FastAPI** REST API
- **FastMCP** MCP server
- **MongoDB** 3-member replica set
- **Kubernetes Deployments** for frontend and API
- **Kubernetes StatefulSet + PVCs** for MongoDB
- **Kubernetes Services** for internal networking/load balancing
- **NGINX Ingress** for routing
- **Minikube** for the local Kubernetes cluster

## Project Structure

```text
fastapi-fastmcp-k8s/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── mcp_server.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── nginx/
│   ├── package.json
│   ├── astro.config.mjs
│   └── Dockerfile
└── k8s/
    ├── mongo.yaml
    ├── api.yaml
    ├── frontend.yaml
    └── ingress.yaml
```

## 1. Prerequisites

```bash
docker --version
minikube version
kubectl version --client
```

Optional, for MCP CLI testing:

```bash
fastmcp --version
```

## 2. Clone the Repository

```bash
git clone https://github.com/hussam-cheema/fastapi-fastmcp-k8s.git
cd fastapi-fastmcp-k8s
```

## 3. Start Minikube

```bash
minikube start
minikube status
kubectl get nodes
```

## 4. Enable NGINX Ingress

```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
kubectl get ingressclass
```

Wait until the NGINX ingress controller is `1/1 Running`.

## 5. Build the Backend Image

From the repository root:

```bash
minikube image build -t fastapi-mcp-demo:2.0 ./backend
minikube image ls | grep fastapi-mcp-demo
```

`k8s/api.yaml` should use:

```yaml
image: fastapi-mcp-demo:2.0
imagePullPolicy: IfNotPresent
```

## 6. Build the Frontend Image

```bash
minikube image build -t reminders-frontend:1.0 ./frontend
minikube image ls | grep reminders-frontend
```

`k8s/frontend.yaml` should use:

```yaml
image: reminders-frontend:1.0
imagePullPolicy: IfNotPresent
```

## 7. Create the Namespace

```bash
kubectl create namespace practice
```

## 8. Deploy MongoDB

```bash
kubectl apply -f k8s/mongo.yaml
kubectl get pods -n practice -l app=mongo -w
```

After all 3 MongoDB pods are running, press `Ctrl+C`.

Check the StatefulSet and storage:

```bash
kubectl get statefulset -n practice
kubectl get pvc -n practice
```

Expected MongoDB members:

```text
mongo-0
mongo-1
mongo-2
```

Expected PVCs:

```text
mongo-data-mongo-0
mongo-data-mongo-1
mongo-data-mongo-2
```

## 9. Initialize the MongoDB Replica Set

Run this only on a fresh deployment:

```bash
kubectl exec -n practice mongo-0 -- mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    {_id: 0, host: "mongo-0.mongo:27017"},
    {_id: 1, host: "mongo-1.mongo:27017"},
    {_id: 2, host: "mongo-2.mongo:27017"}
  ]
})
'
```

Verify:

```bash
kubectl exec -n practice mongo-0 -- mongosh --eval 'rs.status()'
```

You should eventually have one `PRIMARY` and two `SECONDARY` members.

## 10. Deploy FastAPI + FastMCP

Make sure the MongoDB URL in `k8s/api.yaml` is on one line:

```yaml
value: "mongodb://mongo-0.mongo:27017,mongo-1.mongo:27017,mongo-2.mongo:27017/?replicaSet=rs0"
```

Deploy:

```bash
kubectl apply -f k8s/api.yaml
kubectl rollout status deployment/api -n practice
kubectl get pods -n practice -l app=api
```

Expected: 3 API pods ready.

## 11. Deploy the Astro Frontend

```bash
kubectl apply -f k8s/frontend.yaml
kubectl rollout status deployment/frontend -n practice
kubectl get pods -n practice -l app=frontend
```

Expected: 2 frontend pods ready.

## 12. Deploy the Ingress

Make sure `k8s/ingress.yaml` uses:

```yaml
ingressClassName: nginx
```

and:

```yaml
host: reminders.test
```

Apply:

```bash
kubectl apply -f k8s/ingress.yaml
kubectl get ingress -n practice
kubectl describe ingress reminders -n practice
```

Routing should be:

```text
/               -> frontend service
/api            -> api service
/docs           -> api service
/openapi.json   -> api service
/health         -> api service
/mcp            -> api service
```

## 13. Verify All Resources

```bash
kubectl get all -n practice
kubectl get svc -n practice
kubectl get ingress -n practice
kubectl get pvc -n practice
kubectl get deployment -n practice
kubectl get statefulset -n practice
```

Expected application/database pods:

```text
2 Astro frontend pods
3 FastAPI/FastMCP pods
3 MongoDB pods
```

## 14. Start the Minikube Tunnel

In a separate terminal:

```bash
minikube tunnel
```

Enter your macOS password when requested and leave this terminal running.

## 15. Configure the Local Domain

Run once:

```bash
echo "127.0.0.1 reminders.test" | sudo tee -a /etc/hosts
grep reminders.test /etc/hosts
```

Expected:

```text
127.0.0.1 reminders.test
```

## 16. Open the Application

```bash
open http://reminders.test
```

## 17. Test FastAPI Health

```bash
curl http://reminders.test/health/live
curl http://reminders.test/health/ready
```

Example response:

```json
{
  "status": "alive",
  "pod": "api-xxxxxxxxxx-xxxxx"
}
```

## 18. Open Swagger

```bash
open http://reminders.test/docs
```

The API exposes:

```text
GET     /api/reminders
GET     /api/reminders/{id}
POST    /api/reminders
PUT     /api/reminders/{id}
DELETE  /api/reminders/{id}
```

## 19. Test CRUD with REST

Create:

```bash
curl -X POST   http://reminders.test/api/reminders   -H "Content-Type: application/json"   -d '{
    "title": "Learn Kubernetes",
    "description": "Practice Deployments, StatefulSets and Ingress"
  }'
```

List:

```bash
curl http://reminders.test/api/reminders
```

Get one:

```bash
curl http://reminders.test/api/reminders/<REMINDER_ID>
```

Update:

```bash
curl -X PUT   http://reminders.test/api/reminders/<REMINDER_ID>   -H "Content-Type: application/json"   -d '{"completed": true}'
```

Delete:

```bash
curl -X DELETE   http://reminders.test/api/reminders/<REMINDER_ID>
```

## 20. Test FastMCP

MCP endpoint:

```text
http://reminders.test/mcp/
```

List tools:

```bash
fastmcp list   http://reminders.test/mcp/   --auth none
```

Expected tools:

```text
list_reminders
get_reminder
create_reminder
update_reminder
delete_reminder
```

Create through MCP:

```bash
fastmcp call   http://reminders.test/mcp/   create_reminder   title="Learn FastMCP"   description="Created through MCP"   --auth none
```

Reload `http://reminders.test`; the MCP-created reminder should appear because REST and MCP use the same MongoDB data.

## 21. Test API Load Balancing

```bash
for i in {1..10}; do
  curl -s http://reminders.test/health/live
  echo
done
```

Different requests may show different API pod names.

## 22. Useful Logs and Debugging Commands

API logs:

```bash
kubectl logs -n practice deployment/api
kubectl logs -n practice deployment/api -f
```

Frontend logs:

```bash
kubectl logs -n practice deployment/frontend
```

MongoDB logs:

```bash
kubectl logs -n practice mongo-0
```

All pods:

```bash
kubectl get pods -n practice
```

Describe a pod:

```bash
kubectl describe pod -n practice <POD_NAME>
```

Previous crash logs:

```bash
kubectl logs -n practice <POD_NAME> --previous
```

Ingress:

```bash
kubectl get ingress -n practice
kubectl describe ingress reminders -n practice
kubectl get pods -n ingress-nginx
```

MongoDB:

```bash
kubectl exec -n practice mongo-0 -- mongosh --eval 'rs.status()'
kubectl get pvc -n practice
```

Check images used by API pods:

```bash
kubectl get pods -n practice -l app=api   -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image
```

Check frontend images:

```bash
kubectl get pods -n practice -l app=frontend   -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image
```

## 23. Update Backend Code

Build a new tag:

```bash
minikube image build -t fastapi-mcp-demo:2.1 ./backend
```

Update `k8s/api.yaml`:

```yaml
image: fastapi-mcp-demo:2.1
```

Apply and watch the rolling update:

```bash
kubectl apply -f k8s/api.yaml
kubectl rollout status deployment/api -n practice
kubectl get pods -n practice -l app=api
```

## 24. Update Frontend Code

```bash
minikube image build -t reminders-frontend:1.1 ./frontend
```

Update `k8s/frontend.yaml`:

```yaml
image: reminders-frontend:1.1
```

Then:

```bash
kubectl apply -f k8s/frontend.yaml
kubectl rollout status deployment/frontend -n practice
```

## 25. Scale the API

Scale to 5:

```bash
kubectl scale deployment api --replicas=5 -n practice
kubectl get pods -n practice -l app=api
```

Scale back to 3:

```bash
kubectl scale deployment api --replicas=3 -n practice
```

## 26. Destroy All Project Resources

The cleanest reset is:

```bash
kubectl delete namespace practice
```

This removes the project's Deployments, Pods, Services, Ingress, MongoDB StatefulSet and PVCs.

Because the PVCs are deleted with the namespace, MongoDB data in this practice environment is also removed.

Verify:

```bash
kubectl get namespace practice
```

## 27. Stop the Tunnel

In the terminal running:

```bash
minikube tunnel
```

press:

```text
Ctrl+C
```

## 28. Run Everything Again After Destroying the Namespace

```bash
kubectl create namespace practice
kubectl apply -f k8s/mongo.yaml
kubectl get pods -n practice -l app=mongo -w
```

After MongoDB is ready, initialize the fresh replica set:

```bash
kubectl exec -n practice mongo-0 -- mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    {_id: 0, host: "mongo-0.mongo:27017"},
    {_id: 1, host: "mongo-1.mongo:27017"},
    {_id: 2, host: "mongo-2.mongo:27017"}
  ]
})
'
```

Deploy the remaining resources:

```bash
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

Verify:

```bash
kubectl get pods -n practice
kubectl get svc -n practice
kubectl get ingress -n practice
kubectl get pvc -n practice
```

Start the tunnel again in another terminal:

```bash
minikube tunnel
```

Then:

```bash
open http://reminders.test
```

## 29. Completely Destroy Minikube

To remove the entire Minikube cluster:

```bash
minikube delete
```

To recreate it:

```bash
minikube start
minikube addons enable ingress
```

Because `minikube delete` removes Minikube's local images, rebuild them:

```bash
minikube image build -t fastapi-mcp-demo:2.0 ./backend
minikube image build -t reminders-frontend:1.0 ./frontend
```

Then follow the deployment steps again.

## 30. Optional: Remove the Local Host Entry

```bash
sudo nano /etc/hosts
```

Remove:

```text
127.0.0.1 reminders.test
```

## Quick Start

If Minikube already exists, images are already built, NGINX ingress is enabled and `/etc/hosts` is configured:

```bash
kubectl create namespace practice
kubectl apply -f k8s/mongo.yaml
kubectl get pods -n practice -l app=mongo -w
```

Then initialize MongoDB:

```bash
kubectl exec -n practice mongo-0 -- mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    {_id: 0, host: "mongo-0.mongo:27017"},
    {_id: 1, host: "mongo-1.mongo:27017"},
    {_id: 2, host: "mongo-2.mongo:27017"}
  ]
})
'
```

Then:

```bash
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
kubectl get pods -n practice
```

In another terminal:

```bash
minikube tunnel
```

Open:

```bash
open http://reminders.test
```

## Quick Destroy

```bash
kubectl delete namespace practice
```

For a full Minikube reset:

```bash
minikube delete
```
