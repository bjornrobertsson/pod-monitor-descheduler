# pod-monitor-descheduler
POC to show a method to deschedule/terminate a unassigned pod after a pre-defined timeout

To build and deploy this application:

Save/update the Python code, pod_monitor.py, focus on the 'namespace' and 'image' location - this is also where the timeout is configured.
FQDN in the Python script and imagePullSecret in the yaml as well.

Then build and push the Docker image

Finally, create the Kubernetes resources:

kubectl apply -f token.yaml # Create a token in the Coder UI with a 'reasonable' lifetime
kubectl apply -f pod_monitor.yaml

This solution should:

Find pods in the 'coder' namespace that haven't been assigned to a node
If a pod has been without a node for more than 90 seconds, it will:

Try to use the Coder CLI to properly stop the workspace
Delete the pod using the Kubernetes API
Find and delete the parent deployment

