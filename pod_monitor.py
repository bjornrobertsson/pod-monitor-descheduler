#!/usr/bin/env python3

import kubernetes
import time
import os
import logging
from datetime import datetime, timedelta
import subprocess

FQDN_URL='http[s]://Your Coder deployment'

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pod-monitor')

def main():
    # Load Kubernetes configuration from within the cluster
    kubernetes.config.load_incluster_config()
    v1 = kubernetes.client.CoreV1Api()
    apps_v1 = kubernetes.client.AppsV1Api()
    
    token_path = "/tmp/token.txt"
    
    logger.info("Starting pod monitor for namespace 'coder'")
    
    while True:
        try:
            # Get all pods in the 'coder' namespace
            pods = v1.list_namespaced_pod(namespace="coder")
            
            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_namespace = pod.metadata.namespace
                creation_time = pod.metadata.creation_timestamp
                
                # Check if the pod has a node assigned
                if pod.spec.node_name is None:
                    # Calculate age of pod
                    age = datetime.now(creation_time.tzinfo) - creation_time
                    
                    # If pod is older than 90 seconds and still doesn't have a node
                    if age > timedelta(seconds=90):
                        logger.info(f"Pod {pod_name} has been pending for {age} without a node assignment")
                        
                        # Check for the Coder-specific labels
                        labels = pod.metadata.labels or {}
                        username = labels.get("com.coder.user.username")
                        workspace_name = labels.get("com.coder.workspace.name")
                        
                        if username and workspace_name:
                            logger.info(f"Found Coder workspace: user={username}, workspace={workspace_name}")
                            try:
                                # Try using coder CLI to stop the workspace
                                if os.path.exists(token_path):
                                    cmd = f"cat {token_path} | coder login --use-token-as-session {FQDN_URL} && echo yes | coder stop {username}/{workspace_name}"
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                    logger.info(f"Coder stop command result: {result.stdout}")
                                    if result.stderr:
                                        logger.error(f"Coder stop command error: {result.stderr}")
                                else:
                                    logger.warning(f"Token file not found at {token_path}")
                            except Exception as e:
                                logger.error(f"Error stopping workspace via Coder CLI: {e}")
                        
                        # Delete the pod anyway using Kubernetes API
                        try:
                            time.sleep(30)
                            logger.info(f"Deleting pod {pod_name} in namespace {pod_namespace}")
                            v1.delete_namespaced_pod(name=pod_name, namespace=pod_namespace)
                            
                            # Find and delete the owner deployment
                            for owner_ref in pod.metadata.owner_references or []:
                                if owner_ref.kind == "ReplicaSet":
                                    rs = apps_v1.read_namespaced_replica_set(name=owner_ref.name, namespace=pod_namespace)
                                    for rs_owner in rs.metadata.owner_references or []:
                                        if rs_owner.kind == "Deployment":
                                            logger.info(f"Deleting deployment {rs_owner.name} in namespace {pod_namespace}")
                                            apps_v1.delete_namespaced_deployment(name=rs_owner.name, namespace=pod_namespace)
                        except kubernetes.client.exceptions.ApiException as e:
                            logger.error(f"Error deleting resources: {e}")
            
            # Sleep for a while before checking again
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Sleep a bit longer on error

if __name__ == "__main__":
    main()
