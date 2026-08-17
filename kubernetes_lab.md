

# Canonical Kubernetes lab


This material is copyright of Canonical Limited. This material may be used for personal and noncommercial
use only.

This documentation is copyright of Canonical Limited. You are welcome to display on your
computer, download and print this documentation or to use the hard copy provided to you for
personal, education and non-commercial use only. You must retain copyright, trademark and
other notices unaltered on any copies or printouts you make. Any trademarks, logos an service
marks displayed in this document are property of their owners, whether Canonical or third
parties.

This documentation is provided on an "as is" basis, without warranty of any kind, either express
or implied. Your use of this documentation is at your own risk. Canonical disclaims all warranties
and liability that may result directly or indirectly from the use of this documentation.

## Lab assumptions

The following exercises will be done in a practice lab environment comprised of Virtual Machines on GCP cloud.
The instructor will provide you with a public IP and credentials for a student machine. SSH will be used to connect to 
he student machine. The IP is static and reboot persistent.

The purpose of this lab is to familiarize the student with Kubernetes. Kubernetes version `1.34` will be deployed.



# 1. Kubernetes Basics !heading

Kubernetes is an open-source infrastructure for automating deployment, scaling, and management of containerized
applications. Originally built by Google, it is currently maintained by the Cloud Native Computing Foundation.

The upstream Kubernetes version is comprised of:
  * control plane components:
    * etcd distributed key-value store
    * the API server
    * the Scheduler
    * the Controller Manager
  * worker nodes components:
    * the kubelet
    * the service proxy called kube-proxy
    * the container runtime - containerd

## Canonical Kubernetes

The official distribution of Kubernetes on Ubuntu delivers a pure 'upstream' version of Kubernetes for organizations to
use privately, plus a few more features like key distribution and overlay networking. We work directly with Google to
align with Google's GKE offering.

Like Ubuntu itself, Canonical Kubernetes is free to use, and Canonical backs it up with enterprise support, consulting,
and management services. Canonical makes it secure and easy to deploy, operate, and upgrade.

Canonical Kubernetes works on AWS, Google Cloud, Azure and Oracle Cloud as well as private infrastructure from bare-metal
racks to VMware and OpenStack. Ubuntu is the most widely used platform for container operations, and Canonical offers the
largest ecosystem of Kubernetes partners, solutions and integration options.


## 1.1 Deploy Canonical Kubernetes

We will be using `Juju` to model, deploy and manage a Kubernetes cluster on LXD cloud provider using VMs.

First, install Juju and LXD:

```bash
sudo snap install juju --channel=3.6/stable
sudo snap install lxd --channel=5.21/stable
```

Next, initialized LXD and disable IPv6:

```bash
sudo lxd init --auto
lxc network set lxdbr0 ipv6.address none
lxc network unset lxdbr0 ipv6.nat
```

Then, limit the IP range assigned by LXD:

```bash
NETWORK_CIDR=$(lxc network show lxdbr0 | awk '/ipv4.address:/ {print $2}')
IP_2=$(lxc network show lxdbr0 | awk '/ipv4.address:/ {split($2,a,"[./]"); print a[1]"."a[2]"."a[3]".2"}')
IP_127=$(lxc network show lxdbr0 | awk '/ipv4.address:/ {split($2,a,"[./]"); print a[1]"."a[2]"."a[3]".127"}')
lxc network set lxdbr0 ipv4.dhcp.ranges ${IP_2}-${IP_127}
```

The available clouds can be listed.

```bash
juju clouds

# output
Only clouds with registered credentials are shown.
There are more clouds, use --all to see them.
You can bootstrap a new controller using one of these clouds...

Clouds available on the client:
Cloud      Regions  Default    Type  Credentials  Source    Description
localhost  1        localhost  lxd   0            built-in  LXD Container Hypervisor
```

Juju stores states in `controllers`. Before any workload is deployed, a controller needs to be bootstrapped.

```bash
juju bootstrap --constraints "cores=2 mem=4G virt-type=virtual-machine" localhost lxd-controller
```

After the bootstrap process is completed, check its status.

```bash
juju status -m controller

# output
Model       Controller      Cloud/Region         Version  SLA          Timestamp
controller  lxd-controller  localhost/localhost  3.6.14   unsupported  09:14:29Z

App         Version  Status  Scale  Charm            Channel     Rev  Exposed  Message
controller           active      1  juju-controller  3.6/stable  234  yes

Unit           Workload  Agent  Machine  Public address  Ports      Message
controller/0*  active    idle   0        10.237.75.79    17022/tcp

Machine  State    Address       Inst id        Base          AZ                           Message
0        started  10.237.75.79  juju-0ac7e3-0  ubuntu@24.04  rpopescu.cloudbase.internal  Running
```

Workloads live inside `models`, which is an environment associated with a controller. Create a new model for Kubernetes.

```bash
juju add-model canonical-k8s
```

Juju automatically switched to the new model. Models can be listed with.

```bash
juju models
```

The Juju bundle we're about to deploy is placed into `~/config` folder. There's also an overlay bundle that can provide an external ETCD service.

```bash
cat ~/config/canonical-k8s-bundle.yaml

# output
name: canonical-kubernetes
base: ubuntu@24.04
applications:
  k8s:
    charm: k8s
    channel: 1.34/stable
    num_units: 1
    constraints: cores=2 mem=8G root-disk=100G virt-type=virtual-machine
    options:
      bootstrap-node-taints: |-
        node-role.kubernetes.io/control-plane:NoSchedule
      gateway-enabled: true
      ingress-enabled: true
      load-balancer-enabled: true
      load-balancer-l2-mode: true
      load-balancer-cidrs: <placeholder>
  k8s-worker:
    charm: k8s-worker
    channel: 1.34/stable
    num_units: 1
    constraints: cores=4 mem=16G root-disk=100G virt-type=virtual-machine
relations:
  - ['k8s:k8s-cluster', 'k8s-worker:cluster']
  - ['k8s:containerd', 'k8s-worker:containerd']
  - ['k8s:cos-worker-tokens', 'k8s-worker:cos-tokens']
```

Bundle has a `<placeholder>` that needs to be replaced with the generated network CIDR by the `lxd init` command:

```bash
IP_128_CIDR=$(lxc network show lxdbr0 | awk '/ipv4.address:/ {split($2,a,"[./]"); print a[1]"."a[2]"."a[3]".128/25"}')
sed -i "s|<placeholder>|$IP_128_CIDR|g" ~/config/canonical-k8s-bundle.yaml
```

Once modified, check the current content of the file with:

```bash
cat ~/config/canonical-k8s-bundle.yaml
```

Finally, deploy the cluster from that modified bundle:

```bash
juju deploy ~/config/canonical-k8s-bundle.yaml
```


For more information on the charms, please visit:

https://charmhub.io/canonical-kubernetes

Track the deployment process. The deployment can take around 10 minutes. During this time,
the various components can enter block or maintenance state in juju. This is normal, some charms are dependent on other
charms to deploy first. In the end, all charms should become available.

```bash
watch -c juju status --color
```

After the deployment process is done, run `juju status`, it should look like this:

```bash
juju status

# output
Model          Controller      Cloud/Region         Version  SLA          Timestamp
canonical-k8s  lxd-controller  localhost/localhost  3.6.14   unsupported  09:24:48Z

App         Version  Status  Scale  Charm       Channel       Rev  Exposed  Message
k8s         1.34.3   active      1  k8s         1.34/stable  1844  no       Ready
k8s-worker  1.34.3   active      1  k8s-worker  1.34/stable  1841  no       Ready

Unit           Workload  Agent  Machine  Public address  Ports     Message
k8s-worker/0*  active    idle   1        10.237.75.27              Ready
k8s/0*         active    idle   0        10.237.75.10    6443/tcp  Ready

Machine  State    Address       Inst id        Base          AZ                           Message
0        started  10.237.75.10  juju-f36b6c-0  ubuntu@24.04  rpopescu.cloudbase.internal  Running
1        started  10.237.75.27  juju-f36b6c-1  ubuntu@24.04  rpopescu.cloudbase.internal  Running
```

Kubernetes is now deployed, all of this was modeled via the bundle file.

**NOTE**: on your environment the IPs will be different.

## 1.2 Interacting with the cluster and observability

After the cluster is deployed you may assume control over the Kubernetes
cluster from any k8s node.

`kubectl` is the command line tool for Kubernetes. It controls the Kubernetes cluster manager.

`config` are files used to organize information about clusters, users, namespaces, and authentication mechanisms.
The `kubectl` command-line tool uses `config` files to find the information it needs to choose a cluster and communicate
with the API server of a cluster. By default, the config files are created on the `k8s` nodes. Create
the `kubectl` config directory and copy the `config` file to the default location:

```bash
mkdir -p ~/.kube && cd ~/.kube
```

Generate the kubeconfig from the `k8s/leader` unit and save it under its default local folder:

**NOTE** We also need `yq` installed. We're going to install it from a snap.

```bash
sudo snap install yq
juju run k8s/leader get-kubeconfig | yq eval '.kubeconfig' > ~/.kube/config
chmod 600 ~/.kube/config
```

Multiple clusters can be managed with the help of `config` file. Users can switch between different clusters. For more information on
this please visit:

https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters


**Note**: A file that is used to configure access to a cluster is also sometimes called a `kubeconfig` file. This is just a
generic way of referring to configuration files. It does not mean that there is a file named `kubeconfig`.


`kubectl` is the CLI tools to interact with Kubernetes. Install `kubectl` locally:

```bash
sudo snap install kubectl --channel=1.34/stable --classic
```

For information on how to install `kubectl` on other systems, please visit the links:

https://kubernetes.io/docs/tasks/tools/install-kubectl

https://ubuntu.com/kubernetes/docs/operations


Good documentation on `kubectl` can be found here:

https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands

Also, let's add command autocompletion for `kubectl`:

```bash
kubectl completion bash | sudo tee /etc/bash_completion.d/kubectl > /dev/null
sudo chmod a+r /etc/bash_completion.d/kubectl
```

After that, let's logout and re-login:

```bash
exit

ssh ubuntu@<public IP address of your lab>
```

Query the cluster:

```bash
kubectl cluster-info

#output
Kubernetes control plane is running at https://10.237.75.10:6443
CoreDNS is running at https://10.237.75.10:6443/api/v1/namespaces/kube-system/services/coredns:udp-53/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

Kubernetes components like the scheduler or the distributed database can be checked to ensure cluster functionality:

```bash
kubectl get --raw='/readyz?verbose'

# output
[+]ping ok
[+]log ok
[+]etcd ok
[+]etcd-readiness ok
[+]informer-sync ok
[+]poststarthook/start-apiserver-admission-initializer ok
[+]poststarthook/generic-apiserver-start-informers ok
[+]poststarthook/priority-and-fairness-config-consumer ok
[+]poststarthook/priority-and-fairness-filter ok
[+]poststarthook/storage-object-count-tracker-hook ok
[+]poststarthook/start-apiextensions-informers ok
[+]poststarthook/start-apiextensions-controllers ok
[+]poststarthook/crd-informer-synced ok
[+]poststarthook/start-system-namespaces-controller ok
[+]poststarthook/start-cluster-authentication-info-controller ok
[+]poststarthook/start-kube-apiserver-identity-lease-controller ok
[+]poststarthook/start-kube-apiserver-identity-lease-garbage-collector ok
[+]poststarthook/start-legacy-token-tracking-controller ok
[+]poststarthook/start-service-ip-repair-controllers ok
[+]poststarthook/rbac/bootstrap-roles ok
[+]poststarthook/scheduling/bootstrap-system-priority-classes ok
[+]poststarthook/priority-and-fairness-config-producer ok
[+]poststarthook/bootstrap-controller ok
[+]poststarthook/start-kubernetes-service-cidr-controller ok
[+]poststarthook/aggregator-reload-proxy-client-cert ok
[+]poststarthook/start-kube-aggregator-informers ok
[+]poststarthook/apiservice-status-local-available-controller ok
[+]poststarthook/apiservice-status-remote-available-controller ok
[+]poststarthook/apiservice-registration-controller ok
[+]poststarthook/apiservice-discovery-controller ok
[+]poststarthook/kube-apiserver-autoregistration ok
[+]autoregister-completion ok
[+]poststarthook/apiservice-openapi-controller ok
[+]poststarthook/apiservice-openapiv3-controller ok
[+]shutdown ok
readyz check passed
```

In Kubernetes terminology, the workers which run the `kubelet` service are called `nodes`. This cluster is modeled
with one purely worker `node` and one control plane `node` that also runs `kubelet`, but more can be added at any time:

```bash
kubectl get nodes

# output
NAME            STATUS   ROLES                  AGE     VERSION
juju-f36b6c-0   Ready    control-plane,worker   6m33s   v1.34.3
juju-f36b6c-1   Ready    worker                 5m23s   v1.34.3
```

You can get even more detailed information by running `kubectl get nodes -o wide`.

Additionally, check a specific node status, CPU and memory data, system information:

```bash
kubectl describe node <node_name>
```

We can check how much resources are consumed (current resource usage) on each node:

```bash
kubectl top nodes

# output
NAME            CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
juju-f36b6c-0   118m         2%       1479Mi          9%
juju-f36b6c-1   72m          0%       996Mi           3%
```

Resource utilization per pod can also be inspected. You may get an error in the beginning, don't worry,
the metrics take some time to be collected, try again in a minute:

```bash
kubectl top pods --all-namespaces
```

![bundle](assets/k8s_architecture.png)


## 1.3 Pods and namespaces

A `pod` is smallest deployment unit that a user can create. It is an encapsulation of one or more containers
with a shared network and storage scope. The shared context of a pod is implemented with Linux namespaces,
cgroups, among others, the same used for Docker or Containerd containers isolation.

Containers within a pod share an IP address and a port space, of the pod. They communicate with each other inside pods
using standard IPC. Containers in different pods have distinct IPs and communicate on that IP.

Using pods, applications can be designed in a highly distributed manner. Microservice architectures are common for
applications that run on Kubernetes.

Pods are considerate to have ephemeral life and should be treated like cattle. Another important mention is that pods alone
do not offer application high availability. For that, kubernetes has mechanism that make use of pods, but more of that later.

List the pods:

```bash
kubectl get pods -o wide --all-namespaces
```

Multiple pods can be seen, buy why? Kubernetes itself runs it's services (api server, dashboard, etc.) inside
pods. Those pods run in a special namespace called `kube-system`, a system reserved namespace. `Namespaces` are a way
to create scopes for different projects. For example, the development team can work in their `dev` namespace, and the
support team can work in their `support` namespace. The two can be considered different projects, resources are not shared
and the two namespaces are isolated from each other.

By default, a `default` namespace is created along with the kube-system one. List all the namespaces:

```bash
kubectl get namespaces
```

## 1.4 Work with pods and volumes

Kubernetes treats everything as objects, including pods, and each object has a definition. A definition is a declaration of
a desired state. Kubernetes ensures that the current state matches the desired state. For example, when you create a Pod and
declare that the containers in it to be running. If the containers are not running due to an app failure, kubernetes will
recreate the pod in order to drive the pod to desired state.

![bundle](assets/pod1.png)

Take a look at this simple nginx pod definition. The definition is present in a file in `~/resources/nginx-pod.yaml`:

```bash
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
      - containerPort: 80
```

Create the pod:

```bash
kubectl create -f ~/resources/nginx-pod.yaml
```

List the pods and describe the newly created pod, try to understand what is in there and talk with the trainer on the bits
that you do not understand:

```bash
kubectl get pods -o wide
```

```bash
kubectl describe pod nginx
```

Delete the pod:

```bash
kubectl delete pod nginx
```

That's good for a simple web server, but what if persistent storage is needed? The container file system only lives as
long as the container does. Volumes should be used for any persistent storage needs.

There are many volume types available, with some being cloud platform specific (e.g. `azureDisk`, `gcePersistentDisk`,
`azureDisk`, `awsElasticBlockStore`). The standard types include:

`EmptyDir`: is first created when a Pod is assigned to a Node, and exists as long as that Pod is running on that node.
It is initially empty and is stored on whatever medium is backing the node - that might be disk or HDD/SSD or network storage,
depending on your environment.

`HostPath`: Mounts an existing directory on the node’s file system. For example `/var/logs`.


Here is an example of how volumes will look like in a pod definition:

```bash
apiVersion: v1
kind: Pod
metadata:
  name: redis
spec:
  containers:
  - name: redis
    image: redis
    volumeMounts:
    - name: redis-storage
      mountPath: /data/redis
  volumes:
  - name: redis-storage
    emptyDir: {}
```

Create the pod in `~/resources/redis-volume-pod.yaml` and run the `describe pod` command on it afterwards to see
the volumes attached. Delete the pod once done.

```bash
kubectl create -f ~/resources/redis-volume-pod.yaml
```

```bash
kubectl describe pod redis
```

Multiple containers can also exist in one pod. Take a look at this example:

```bash
cat ~/resources/multi-container-pod.yaml
```

There are two containers, `nginx-container` and `debian-container`. The `debian-container` is responsible for generating the index file, while `nginx-container` serves it to the clients.

Finally, delete the pod:

```bash
kubectl delete pod redis
```

![bundle](assets/pod2.png)


# 2. Networking !heading

## 2.1 Exposing apps using Services and Labels

The pods/apps we've created so far were not accessible. Kubernetes does not follow the legacy networking architecture
because of a number of reasons:

  * pods are ephemeral
  * Kubernetes itself assigns IPs to pods after they are scheduled -> the user cannot assign or know the IP beforehand
  * scaling and load-balancing: users should not care how many pods are backing a service, what their IPs are, on which nodes the pods are scheduled

To solve these issues, Kubernetes provides the `Service` object resource type.

![service](assets/network1.png)

A `Service` is a single point of access to a group of pods that provide the same type of service. Each service has
an IP and a port that will never change during the lifetime of the service. Users will initiate connections to the IP
and port, and those connections are routed to one of the pods backing the service. This way, users don't have to care
about pod location and if a pod crashes.

![service](assets/service1.png)


There are three types of Services:
  * `ClusterIPs`: the purpose of this type of service is exposing groups of pods to other pods in the cluster
  * `NodePort`: allocates a static port on the Node on which the pod is running. Used to access Pod port from outside the cluster
  * `LoadBalancer`: exposes the service externally using a cloud provider’s load balancer. Used to access Pod's from outside the cluster
  * `ExternalName`: maps the Service to the contents of the externalName field (for example, to the hostname api.foo.bar.example). The mapping configures your cluster's DNS server to return a CNAME record with that external hostname value. No proxying of any kind is set up.

`Labels` and `Selectors` help in associating Services to Pods. `Labels` are key-value pairs that can be associated with pods in the pod
definition. Then, a Service will use label `Selectors` to know to which pods to redirect traffic to.

For example, given some pods running an app, we would specify in the pod definition of the app we specify a label `app: nginx` and we
scale the pods to 3. Then a service can be create with Selector `app: nginx`. This is how Services know where to route traffic
and load-balance between the 3 pods.

![labels and selectors](assets/labels_selectors.png)

Let's take a look at the existing services:

```bash
kubectl get svc --all-namespaces

# output
NAMESPACE        NAME                                TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)                      AGE
default          kubernetes                          ClusterIP      10.152.183.1     <none>          443/TCP                      7m28s
kube-system      cilium-ingress                      LoadBalancer   10.152.183.47    10.237.75.128   80:32392/TCP,443:32446/TCP   7m2s
kube-system      ck-storage-rawfile-csi-controller   ClusterIP      None             <none>          <none>                       7m23s
kube-system      ck-storage-rawfile-csi-node         ClusterIP      10.152.183.168   <none>          9100/TCP                     7m23s
kube-system      coredns                             ClusterIP      10.152.183.68    <none>          53/UDP,53/TCP                7m24s
kube-system      hubble-peer                         ClusterIP      10.152.183.184   <none>          443/TCP                      7m5s
kube-system      metrics-server                      ClusterIP      10.152.183.77    <none>          443/TCP                      7m24s
metallb-system   metallb-webhook-service             ClusterIP      10.152.183.169   <none>          443/TCP                      7m23s
```

Here we can see all the Services within the cluster. Control plane Kubernetes Pods talk to each other via the `ClusterIPs`. Only the `cilium-ingress` service is exposed to the outside world. If you add `-o wide` to the command above, you can see in the `Selector` field the association between a Service and Pods.
The `ClusterIPs` are internal, virtual IPs that only Kubernetes has knowledge of.

**NOTE**: The same Selector mechanism is used for other objects (resources) offered by Kubernetes. Other Kubernetes objects (Deployment,
ReplicaSets, etc,) which interact with Pods use the same mechanism.

Ok, let's redeploy `nginx` and use a label. Check the `~/resources/nginx-pod.yaml` pod definition to see and note the `label` part:

```bash
cat ~/resources/nginx-pod.yaml

# output
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
      - containerPort: 80
```

```bash
kubectl create -f ~/resources/nginx-pod.yaml
```

Now it's time to create the Service. The Service definition file should be found under `~/resources/nginx-service.yaml`. Let's
examine the contents and create the Service:

```bash
cat ~/resources/nginx-service.yaml

# output
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  ports:
  - port: 8080
    targetPort: 80
  selector:
    app: nginx
```

```bash
kubectl create -f ~/resources/nginx-service.yaml
```

The service should now be visible:

```bash
kubectl get svc -o wide

# output
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE    SELECTOR
kubernetes   ClusterIP   10.152.183.1     <none>        443/TCP    9m7s   <none>
nginx        ClusterIP   10.152.183.150   <none>        8080/TCP   63s    app=nginx
```

Currently, the app can now be accessed from within the cluster, but not from outside of the cluster.

Actually, there are two ways to probe the web app, but both of them are just for demonstration purposes. In production
environments direct access to the apps is desired, we do not have that yet. This is just for demonstration purposes and to
understand the architecture.

One of the rules of Kubernetes networking is: all nodes can communicate with all containers without NAT. This means that if we `ssh` in
one of the Nodes, we should be able to `curl` the web app. For this two things are needed, the `ClusterIP` of the app and the
port on which the app is listening, both of which we can extract from the previous `kubectl get svc -o wide` command. We need to
log in one of the Nodes , doesn't matter which one, all the Nodes can reach the Pod. List the nodes:

```bash
juju status k8s-worker

# output
...
Unit           Workload  Agent  Machine  Public address  Ports  Message
k8s-worker/0*  active    idle   1        10.237.75.27           Ready

Machine  State    Address       Inst id        Base          AZ                           Message
1        started  10.237.75.27  juju-f36b6c-1  ubuntu@24.04  rpopescu.cloudbase.internal  Running
```

Machine `1` should do it:

```bash
juju ssh 1
```

```bash
sudo apt install -y pandoc
curl -s 10.152.183.150:8080 | pandoc -f html -t plain

# output
Welcome to nginx!

If you see this page, nginx is successfully installed and working.
Further configuration is required for the web server, reverse proxy, API
gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security
features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

```bash
# exit k8s-worker node
exit
```

This should also work from the control plane node, as it doesn't have any taints that would prevent scheduling.

```bash
juju ssh 0
```

```bash
sudo apt install -y pandoc
curl -s 10.152.183.150:8080 | pandoc -f html -t plain

# output
Welcome to nginx!

If you see this page, nginx is successfully installed and working.
Further configuration is required for the web server, reverse proxy, API
gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security
features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

Go back to the student machine:

```bash
exit
```

## 2.2 Service discovery

Another rule of Kubernetes networking is: all containers can communicate with all the other containers without NAT. This means that
the web app can be probed from another pod with a `ClusterIP` associated with it. But for this we won't be using the `ClusterIP`,
but the DNS record of the Service.

Pods need to talk to each other. Kubernetes has multiple mechanisms to do this. One of them is to set the `ClusterIPs` as environment
variables inside the pods. In this way, when some frontend component needs to talk to the backend, for example, the IP and port can be
referenced from the environment variable. In the nginx example, it would look like this `NGINX_SERVICE_HOST=10.152.183.197`
and `NGINX_SERVICE_PORT=8080`. This is not the best approach, however. If you add a new Service, it will not be automatically
be set on already running pods.

Another method is to have a DNS server in a Pod. Canonical Kubernetes comes with this feature by default. All the pods in the cluster are automatically
configured to use the DNS server (`/etc/resolv.conf` file). In this way, any query performed by a process within a Pod will be handled
by DNS server in Kubernetes, which is accessible from the whole cluster.

The default DNS server in Kubernetes is CoreDNS. It runs as a pod in the `kube-system` namespace.More info can be found here https://coredns.io.

If the DNS server is present, when a Service is created for a Pod, a  `A record` is also associated with the Pod in the form of
`pod-ip-address.my-namespace.pod.cluster.local`. For example, if I have a Pod with the ClusterIP of `1.2.3.4` in the `default`
Namespace, the DNS entry will be `1.2.3.4.default.pod.cluster.local`.

Alongside the previous nginx pod and service, we'll create another pod and do a `curl` on the nginx record from there. Commands can
be ran directly inside a pod by using `kubectl exec`. You can also lunch an interactive bash shell inside a pod (granted if the
base container has the bash installed).

List the `CoreDNS` pod:

```bash
kubectl get pods -n kube-system | { head -n 1; grep "coredns"; }

# output
NAME                                  READY   STATUS    RESTARTS   AGE
coredns-6bb97769df-dstl9              1/1     Running   0          11m
```

The pod can be created without a pods definition file:

```bash
kubectl run shell -i --tty --image ubuntu -- /bin/bash
```

```bash
# exit pod
root@shell:/# exit
```

After which we can reconnect to the pod:

```bash
kubectl exec -it shell -- /bin/bash
```

```bash
root@shell:/# apt update
```

```bash
root@shell:/# apt install curl pandoc -y
```

```bash
root@shell:/# curl -s nginx:8080 | pandoc -f html -t plain

# output
Welcome to nginx!

If you see this page, nginx is successfully installed and working.
Further configuration is required for the web server, reverse proxy, API
gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security
features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

```bash
# go back to the student machine
root@shell:/# exit
```

Here `nginx` is the name of the Service:

```bash
kubectl get svc -o wide

# output
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE     SELECTOR
kubernetes   ClusterIP   10.152.183.1     <none>        443/TCP    11m     <none>
nginx        ClusterIP   10.152.183.150   <none>        8080/TCP   3m35s   app=nginx
```

## 2.3 NodePort and LoadBalancer Services

Until now we made the web app available only inside the cluster. There are a couple of ways to allow outside access.

`NodePorts` are one way to do it. Kubernetes will open a port on all Nodes. That port is accessible via the Nodes IP address.

![nodeport](assets/nodeport.png)

This is a `NodePort` Service definition for nginx app:

```bash
cat ~/resources/nodeport-service.yaml

# output
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 80
    nodePort: 30111
  selector:
    app: nginx
```

```bash
kubectl create -f ~/resources/nodeport-service.yaml
```

Inspect the service:

```bash
kubectl get svc -o wide

# output
NAME             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE     SELECTOR
kubernetes       ClusterIP   10.152.183.1     <none>        443/TCP          12m     <none>
nginx            ClusterIP   10.152.183.150   <none>        8080/TCP         3m57s   app=nginx
nginx-nodeport   NodePort    10.152.183.93    <none>        8080:30111/TCP   4s      app=nginx
```

`nodePort: 30111` is of utmost importance here. The connection would look like this `<NodeIP>:<30111>`:

First, install the required `pandoc` so you can interpret HTML output of `curl`:

```bash
sudo apt update && sudo apt install -y pandoc
```

Then, find out the IP address of your nodes, control plane and worker:

```bash
juju status --format short

# output
- k8s/0: 10.237.75.10 (agent:idle, workload:active) 6443/tcp
- k8s-worker/0: 10.237.75.27 (agent:idle, workload:active)
```

Lastly, `curl` any of those nodes to get access to the `nginx` service.

```bash
curl -s 10.237.75.10:30111 | pandoc -f html -t plain

# output
Welcome to nginx!

If you see this page, nginx is successfully installed and working.
Further configuration is required for the web server, reverse proxy, API
gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security
features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

`10.XXX.XXX.XXX` is the management IP of the control plane node `k8s/0`, get your IP by running `juju status` command.

**NOTE**: This required that port `30111` is opened on the Node.

Using NodePorts in production has a number of limitations, including:
 * only possible to have 1 service per port
 * limited Ports Range 30000 to 32767
 * in case of node IP address change the Service becomes unavailable
 * in case the node goes down the Service becomes unavailable

`LoadBalancer` is another type of Service allowing connections from outside. Kubernetes clusters usually run on top of
Cloud providers like AWS, Azure and GCP. Clusters and Cloud providers know how to interact with each other. The Cloud provider
will associate a public IP with the app. In ca local deployment of Canonical Kubernetes, this is handled by `Cilium` and `MetalLB`.

![loadbalancer](assets/loadbalancer2.png)

**NOTE** the IPs and ports from the diagram differ from the exercise ones.

Create a `LoadBalancer` IP and associate it with the nginx app:

```bash
cat ~/resources/loadbalancer-service.yaml

# output
apiVersion: v1
kind: Service
metadata:
  name: nginx-loadbalancer
spec:
  type: LoadBalancer
  ports:
  - port: 8080
    targetPort: 80
  selector:
    app: nginx
```

```bash
kubectl create -f ~/resources/loadbalancer-service.yaml
```

It will take a couple of seconds for `MetalLB` to allocate a Load Balancer. Take a look at services:

```bash
kubectl get svc

# output
NAME                 TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)          AGE
kubernetes           ClusterIP      10.152.183.1     <none>          443/TCP          13m
nginx                ClusterIP      10.152.183.150   <none>          8080/TCP         5m20s
nginx-loadbalancer   LoadBalancer   10.152.183.240   10.237.75.129   8080:30436/TCP   16s
nginx-nodeport       NodePort       10.152.183.93    <none>          8080:30111/TCP   87s
```

`10.237.75.129:8080` is a "public" IP address allocated by `MetalLB`. Try to access it from a tunneled browser.
Also, from any of the nodes, including your host, you can run:

```bash
curl -s 10.237.75.129:8080 | pandoc -f html -t plain
```

Cleanup the resources created so far:

```bash
# run 'kubectl get svc' to get the services
kubectl delete svc nginx nginx-loadbalancer nginx-nodeport
```

```bash
# run 'kubectl get pods' to get the pods
kubectl delete pod nginx shell
```

## 2.4 Ingress controllers

Ingress resources are DNS mappings to your containers, routed through endpoints. They can manage external access to the services
in a cluster, providing load balancing, name-based virtual hosting and SSL termination.

![ingress](assets/ingress2.png)

Canonical Kubernetes comes with Cilium CNI. Cilium provides different type of services and use-cases to your Kubernetes cluster, including `ingresses`.

Check the Cilium pods are running on each node:

```bash
kubectl get pods -A -o wide | awk 'NR==1 || tolower($0) ~ /cilium/'

# output
NAMESPACE        NAME                                  READY   STATUS    RESTARTS   AGE   IP             NODE            NOMINATED NODE   READINESS GATES
kube-system      cilium-k99m6                          1/1     Running   0          53m   10.237.75.27   juju-f36b6c-1   <none>           <none>
kube-system      cilium-operator-555fdf7495-xjvfm      1/1     Running   0          54m   10.237.75.10   juju-f36b6c-0   <none>           <none>
kube-system      cilium-qvhr6                          1/1     Running   0          54m   10.237.75.10   juju-f36b6c-0   <none>           <none>
```

```bash
kubectl get svc -A |  awk 'NR==1 || tolower($0) ~ /cilium/'

# output
NAMESPACE        NAME                                TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)                      AGE
kube-system      cilium-ingress                      LoadBalancer   10.152.183.47    10.237.75.128   80:32392/TCP,443:32446/TCP   61m
```

Let's imagine we have a web application with two microservices, red and blue. The microservices are just displaying some text, but from a design perspective, a real world application would work just the same.

Check the red microservice definition:

```bash
cat ~/resources/red-app.yaml

# output
kind: Pod
apiVersion: v1
metadata:
  name: red-app
  labels:
    app: red
spec:
  containers:
    - name: red-app
      image: hashicorp/http-echo
      args:
        - "-text=red-microservice"
---
kind: Service
apiVersion: v1
metadata:
  name: red-service
spec:
  selector:
    app: red
  ports:
    - port: 5678
```

The blue microservice looks the same but instead of red, it displays blue.

Also, check the Ingress Controller definition:

```bash
cat ~/resources/ingress.yaml

# output
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bluered-ingress
  annotations:
    ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: cilium
  rules:
  - http:
      paths:
        - path: /blue
          pathType: Prefix
          backend:
            service:
              name: blue-service
              port:
                number: 5678
        - path: /red
          pathType: Prefix
          backend:
            service:
              name: red-service
              port:
                number: 5678
```

Each HTTP rule contains the following information:
1. An optional `host`. If no host is specified, the rule applies to all inbound HTTP traffic through the IP address specified.

2. A list of paths (`/red`, `/blue`), each of which has an associated backend defined with a service. Both the host and path must match
the content of an incoming request before the load balancer directs traffic to the referenced Service.

3. A backend - combination of Service and port names as described in the Service. Requests to the Ingress that matches the host and
path of the rule are sent to the listed backend.

Create the objects:

```bash
kubectl create -f ~/resources/blue-app.yaml
kubectl create -f ~/resources/red-app.yaml
kubectl create -f ~/resources/ingress.yaml
```

The Ingress Controller is created:

```bash
kubectl get ingress

# output 
NAME              CLASS    HOSTS   ADDRESS         PORTS   AGE
bluered-ingress   cilium   *       10.237.75.128   80      78s
```

`10.237.75.128 ` is the MetalLB IP address for this ingress. It's matching the IP address of the `cilium-ingress` service from above. Open your tunneled browser and navigate to `http://10.237.75.128/blue` and `http://10.237.75.128/red`.

**NOTE**: your LoadBalancer IP will be different.

After everything is tested, remove the Ingress and pods.

```bash
kubectl delete -f ~/resources/blue-app.yaml
kubectl delete -f ~/resources/red-app.yaml
kubectl delete -f ~/resources/ingress.yaml
```

For more Ingress related information regarding Canonical Kubernetes, please visit:

https://kubernetes.io/docs/concepts/services-networking/ingress/
https://docs.cilium.io/en/stable/network/servicemesh/ingress/



# 3. Keeping apps healthy !heading

## 3.1 ReplicaSets

A `ReplicaSet` enables us to achieve high availability by ensuring that a specified number of pod replicas are running at any one time.
In other words, a `ReplicaSet` makes sure that a pod or a homogeneous set of pods is always up and available.

If there are too many pods, the `ReplicaSet` terminates the additional pods. If there are too few, the `ReplicaSet` starts more pods.
Unlike manually created pods, the pods maintained by a `ReplicaSet` are automatically replaced if they fail, are deleted, or are terminated.

`ReplicaSet` is often abbreviated to `rs` as a shortcut in `kubectl` commands.

![service](assets/service1.png)

Now we'll create a `ReplicaSet` with this `~/resources/nginx-rs.yaml` definition:

```bash
cat ~/resources/nginx-rs.yaml

# output
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
```

The 3 most important things here are:
  * replica count: which specifies the desired number of pods that should be running
  * label selector: which determines what pods are in the ReplicaSets’s scope
  * pod template: which is used when creating new pod replicas

Create the `rs`:

```bash
kubectl create -f ~/resources/nginx-rs.yaml
```

Inspect the `rs`:

```bash
kubectl get rs nginx-rs -o wide

# output
NAME       DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES         SELECTOR
nginx-rs   3         3         3       9s    nginx        nginx:latest   app=nginx
```

```bash
kubectl describe rs nginx-rs

# output
Name:         nginx-rs
Namespace:    default
Selector:     app=nginx
Labels:       <none>
Annotations:  <none>
Replicas:     3 current / 3 desired
Pods Status:  3 Running / 0 Waiting / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:         nginx:latest
    Port:          80/TCP
    Host Port:     0/TCP
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From                   Message
  ----    ------            ----  ----                   -------
  Normal  SuccessfulCreate  23s   replicaset-controller  Created pod: nginx-rs-b9s4g
  Normal  SuccessfulCreate  23s   replicaset-controller  Created pod: nginx-rs-6vldg
  Normal  SuccessfulCreate  23s   replicaset-controller  Created pod: nginx-rs-47z7s
```

```bash
kubectl get pods

# output
NAME             READY   STATUS    RESTARTS   AGE
nginx-rs-47z7s   1/1     Running   0          55s
nginx-rs-6vldg   1/1     Running   0          55s
nginx-rs-b9s4g   1/1     Running   0          55s
```

Now the application is highly available. They now need a Service to be accessed. We can recreate any type of Service that we
have used before. This is possible because of the Labels and Selectors. The newly create pods have the `app=nginx` label
and the Services we create before point to that label.

Recreate the `LoadBalancer` service:

```bash
kubectl create -f ~/resources/loadbalancer-service.yaml
```

Then, get the LoadBalancer IP address with:

```bash
kubectl get svc nginx-loadbalancer

# output
NAME                 TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)          AGE
nginx-loadbalancer   LoadBalancer   10.152.183.56   10.237.75.129   8080:31036/TCP   40s
```

Then, try accessing the website a few times:

```bash
curl -s 10.237.75.129:8080 | pandoc -f html -t plain

#output
Welcome to nginx!

If you see this page, nginx is successfully installed and working.
Further configuration is required for the web server, reverse proxy, API
gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security
features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

The traffic will now be load balanced between the 3 pods.

To verify that, we can go through the logs of each pod. To do that, run:

```bash
kubectl get pods

# output
NAME             READY   STATUS    RESTARTS   AGE
nginx-rs-47z7s   1/1     Running   0          33m
nginx-rs-6vldg   1/1     Running   0          33m
nginx-rs-b9s4g   1/1     Running   0          33m

kubectl logs nginx-rs-47z7s
kubectl logs nginx-rs-6vldg
kubectl logs nginx-rs-b9s4g
```

You can try to delete a Pod to see what happens. A new Pod should take its place in a few seconds. List the pods and
choose one to delete:

```bash
kubectl get pods
```

```bash
kubectl delete pod nginx-rs-47z7s
```

List the pods again, there is a new pod only some seconds old:

```bash
kubectl get pods

# output
NAME             READY   STATUS    RESTARTS   AGE
nginx-rs-6vldg   1/1     Running   0          34m
nginx-rs-b9s4g   1/1     Running   0          34m
nginx-rs-dgcn6   1/1     Running   0          11s
```

Delete the `rs` and the Service:

```bash
kubectl delete rs nginx-rs
```

```bash
kubectl delete svc nginx-loadbalancer
```

## 3.2 Deployments

All the functionality we have worked with so far can already cover a wide variety of app deployment use cases, but there is more
Kubernetes can do. It can also provide a clan way for applications that run in pods to be upgraded from version to version,
with NO downtime. This is provided through declarative updates for Pods and ReplicaSets.

Kubernetes provides the `Deployment` resource that sits on top of `ReplicaSets`, a declarative way to update Pods. You describe
a desired state in a Deployment object, and the Deployment controller changes the actual state to the desired state at a controlled rate.

![deployment](assets/deployment.png)


Let's take a look on how a Deployment definition looks like, the file is `~/resources/nginx-deploy.yaml`:

```bash
cat ~/resources/nginx-deploy.yaml

# output
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deploy
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.28
        ports:
        - containerPort: 80
```

Again, like in the case of `ReplicaSets`, the most important things are:
  * replica count: which specifies the desired number of pods that should be running
  * label selector: which determines what pods are in the ReplicaSets’s scope
  * pod template: which is used when creating new pod replicas


Create the Deployment:

```bash
kubectl create -f ~/resources/nginx-deploy.yaml
```

Inspect what was creates:

```bash
kubectl get deploy nginx-deploy -o wide

# output
NAME           READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES       SELECTOR
nginx-deploy   3/3     3            3           14s   nginx        nginx:1.28   app=nginx
```

```bash
kubectl describe deploy nginx-deploy

# output
Name:                   nginx-deploy
Namespace:              default
CreationTimestamp:      Wed, 18 Mar 2026 11:27:51 +0000
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:         nginx:1.28
    Port:          80/TCP
    Host Port:     0/TCP
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   nginx-deploy-7f9c8bf8cd (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  24s   deployment-controller  Scaled up replica set nginx-deploy-7f9c8bf8cd from 0 to 3
```

```bash
kubectl get pods

# output
NAME                            READY   STATUS    RESTARTS   AGE
nginx-deploy-7f9c8bf8cd-5srlj   1/1     Running   0          39s
nginx-deploy-7f9c8bf8cd-nmw77   1/1     Running   0          39s
nginx-deploy-7f9c8bf8cd-tqx4m   1/1     Running   0          39s
...
```

So far everything looks similar to the  `ReplicaSets` case. The addition lies in how easily upgrades can be made. First, check the
rollout status. Initially, it should only tell that the deployment was created:

```bash
kubectl rollout status deploy nginx-deploy

# output
deployment "nginx-deploy" successfully rolled out
```

A Deployment `rollout` is a mechanism which allows performing application rolling upgrades. The rollout is triggered if and only if
the Deployment pod template is changed, for example if the image version is changed.

![deployment](assets/rolling_upgrade.png)

Suppose that we now want to update the nginx Pods to use the `nginx:1.29` image instead of the `nginx:1.28` image:

```bash
kubectl set image deploy nginx-deploy nginx=nginx:1.29

# output
deployment.extensions/nginx-deploy image updated
```

**NOTE**: Alternatively, the Deployment definition can be changed with `kubectl edit deploy nginx-deploy` in an interactive manner.
This stands true for all Kubernetes resource types.

Check Deployment status:

```bash
kubectl rollout status deploy nginx-deploy

# output
Waiting for deployment "nginx-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 2 out of 3 new replicas have been updated...
Waiting for deployment "nginx-deploy" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "nginx-deploy" rollout to finish: 1 old replicas are pending termination...
deployment "nginx-deploy" successfully rolled out
#hit CTRL+C
```

```bash
kubectl get deploy -o wide

# output
NAME           READY   UP-TO-DATE   AVAILABLE   AGE    CONTAINERS   IMAGES       SELECTOR
nginx-deploy   3/3     3            3           105s   nginx        nginx:1.29   app=nginx
```

```bash
kubectl get pods

# output
NAME                            READY   STATUS    RESTARTS   AGE
nginx-deploy-578c8ff859-8t46m   1/1     Running   0          44s
nginx-deploy-578c8ff859-jrn9q   1/1     Running   0          45s
nginx-deploy-578c8ff859-spd85   1/1     Running   0          43s
...
```

```bash
kubectl describe deploy nginx-deploy

# output
Name:                   nginx-deploy
Namespace:              default
CreationTimestamp:      Wed, 18 Mar 2026 11:27:51 +0000
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 2
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:         nginx:1.29
    Port:          80/TCP
    Host Port:     0/TCP
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  nginx-deploy-7f9c8bf8cd (0/0 replicas created)
NewReplicaSet:   nginx-deploy-578c8ff859 (3/3 replicas created)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScalingReplicaSet  2m19s  deployment-controller  Scaled up replica set nginx-deploy-7f9c8bf8cd from 0 to 3
  Normal  ScalingReplicaSet  62s    deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 0 to 1
  Normal  ScalingReplicaSet  61s    deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 3 to 2
  Normal  ScalingReplicaSet  61s    deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 1 to 2
  Normal  ScalingReplicaSet  60s    deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 2 to 1
  Normal  ScalingReplicaSet  60s    deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 2 to 3
  Normal  ScalingReplicaSet  59s    deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 1 to 0
```

As can be seen everything is up-to-date and running. The image in use is `nginx:1.29`. The scaling process can also be viewed
on the deployment description `Events` section.

The same Services can be associated with the pods, same as before.

It's important to mention that there are two strategies for upgrading apps with Deployments:
  * `recreate` strategy: old pods are deleted before new ones are created
  * `RollingUpdate` strategy: replace pods step by step

The default one is `RollingUpdate`, the one we used in our case. This works if the application supports two versions of it running at
the same time, for a brief period. The major advantage of this strategy is that there is no downtime. With the `recreate` strategy
there is a downtime brief period between when then the last old version pod was deleted and the first new version pod comes up.

But let's say there is an issue with the current application version that was rolled out. Another powerful feature of `Deployments` is
that they can be rolled back to a previous revision if there are any issues.

Check and inspect the revision history:

```bash
kubectl rollout history deploy nginx-deploy

# output
deployment.apps/nginx-deploy
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

```bash
# this command does not do anything, it just inspects the revision
kubectl rollout history deploy nginx-deploy --revision=1

# output
deployment.apps/nginx-deploy with revision #1
Pod Template:
  Labels:	app=nginx
	pod-template-hash=7f9c8bf8cd
  Containers:
   nginx:
    Image:	nginx:1.28
    Port:	80/TCP
    Host Port:	0/TCP
    Environment:	<none>
    Mounts:	<none>
  Volumes:	<none>
  Node-Selectors:	<none>
  Tolerations:	<none>
```

```bash
# this command does not do anything, it just inspects the revision
kubectl rollout history deploy nginx-deploy --revision=2

# output
deployment.apps/nginx-deploy with revision #2
Pod Template:
  Labels:	app=nginx
	pod-template-hash=578c8ff859
  Containers:
   nginx:
    Image:	nginx:1.29
    Port:	80/TCP
    Host Port:	0/TCP
    Environment:	<none>
    Mounts:	<none>
  Volumes:	<none>
  Node-Selectors:	<none>
  Tolerations:	<none>
```

Revision `1` is the initial deployment version. Revision `2` is the upgraded version.

Rollback to the initial state:

```bash
kubectl rollout undo deploy nginx-deploy --to-revision=1

# output
deployment.extensions/nginx-deploy
```

Check how the Deployment looks like, it should have `nginx:1.28`, the old version:

```bash
kubectl describe deploy nginx-deploy

# output
Name:                   nginx-deploy
Namespace:              default
CreationTimestamp:      Wed, 18 Mar 2026 11:27:51 +0000
Labels:                 app=nginx
Annotations:            deployment.kubernetes.io/revision: 3
Selector:               app=nginx
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=nginx
  Containers:
   nginx:
    Image:         nginx:1.28
    Port:          80/TCP
    Host Port:     0/TCP
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  nginx-deploy-578c8ff859 (0/0 replicas created)
NewReplicaSet:   nginx-deploy-7f9c8bf8cd (3/3 replicas created)
Events:
  Type    Reason             Age                From                   Message
  ----    ------             ----               ----                   -------
  Normal  ScalingReplicaSet  3m48s              deployment-controller  Scaled up replica set nginx-deploy-7f9c8bf8cd from 0 to 3
  Normal  ScalingReplicaSet  2m31s              deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 0 to 1
  Normal  ScalingReplicaSet  2m30s              deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 3 to 2
  Normal  ScalingReplicaSet  2m30s              deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 1 to 2
  Normal  ScalingReplicaSet  2m29s              deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 2 to 1
  Normal  ScalingReplicaSet  2m29s              deployment-controller  Scaled up replica set nginx-deploy-578c8ff859 from 2 to 3
  Normal  ScalingReplicaSet  2m28s              deployment-controller  Scaled down replica set nginx-deploy-7f9c8bf8cd from 1 to 0
  Normal  ScalingReplicaSet  16s                deployment-controller  Scaled up replica set nginx-deploy-7f9c8bf8cd from 0 to 1
  Normal  ScalingReplicaSet  15s                deployment-controller  Scaled down replica set nginx-deploy-578c8ff859 from 3 to 2
  Normal  ScalingReplicaSet  13s (x4 over 15s)  deployment-controller  (combined from similar events): Scaled down replica set nginx-deploy-578c8ff859 from 1 to 0
```

If we check for `ReplicaSets`, we can see the `rs` that backs the `Deployment`:

```bash
kubectl get rs

# output
NAME                      DESIRED   CURRENT   READY   AGE
nginx-deploy-578c8ff859   0         0         0       2m55s
nginx-deploy-7f9c8bf8cd   3         3         3       4m12s
```

Concluding this chapter, we'll need to cleanup the whole deployment:

```bash
kubectl delete deploy nginx-deploy
```


# 4. Storage and User Data !heading

Applications can write and read data directly on and from the container filesystem. This approach can have many drawbacks,
one is when two container of the same pod need to access the same piece of data. Also, Kubernetes works on pod level, so
something new had to be done to address this.

## 4.1 Volumes

`Volumes` are a Kubernetes resource type that solves this. A Volume can be shared between containers of the same pod.
There are different types of volumes, some are ephemeral, meaning that they live as long as the pods do, and some are persistent
on pod deletion.

There are many volume types, but some of the most used are:
  * `emptyDir`: exists as long as that pod does, it is initially empty. By default, emptyDir volumes are stored on whatever medium is backing the node - that might be disk or SSD or network storage, depending on your environment. Privileged containers are required for this type of volume.
  * `hostPath`: mounts a directory from the host Node's filesystem. Useful in some situations: e.g. containers need to access Docker internals or host's `/sys` special filesystem
  * `fc`: allows an existing fibre channel block storage volume to be mounted in a Pod
  * `image`: An image volume source represents an OCI object (a container image or artifact) which is available on the kubelet's host machine.
  * `nfs`: mounts NFS shared into pods
  * `iscsi`: mounts iSCSI volumes into pods

Let's create a Pod with two running containers and a shared `emptyDir` volume. This is how the pod definition
`~/resources/multi-container-pod.yaml` looks like:

```bash
cat ~/resources/multi-container-pod.yaml

# output
apiVersion: v1
kind: Pod
metadata:
  name: two-containers
  labels:
    app: two-containers
spec:
  restartPolicy: Never
  volumes:
  - name: shared-data
    emptyDir: {}
  containers:
  - name: nginx-container
    image: nginx:latest
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html
  - name: debian-container
    image: debian
    volumeMounts:
    - name: shared-data
      mountPath: /pod-data
    command: ["/bin/sh"]
    args: ["-c", "echo Hello from the debian container > /pod-data/index.html; sleep 900000"]
```

The volume is called `shared-data`. Containers reference the volume by name in the `volumeMounts` of the container template.
`mountPath` is from where the volume is accessible from inside the container. As you can see, the first container sees the html file
in `/usr/share/nginx/html/index.html` and the second container in  `/pod-data/index.html`, but it's the same file. Try to understand
the definition file, discuss any interesting details with the trainer.

Create the pod and a service for it, the definition files are already provisioned in `~/resources/multi-container-pod.yaml` and
`~/resources/multi-container-pod-service.yaml`:

```bash
kubectl create -f ~/resources/multi-container-pod.yaml
```

```bash
kubectl create -f ~/resources/multi-container-pod-service.yaml
```

Get the ClusterIP, connect to a Node and `curl` from there:

```bash
kubectl get svc two-containers-svc

# output
NAME                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
two-containers-svc   ClusterIP   10.152.183.236   <none>        8080/TCP   38s
```

SSH into one of the nodes:

```bash
juju ssh 0
```

```bash
curl 10.152.183.236:8080

# output
Hello from the debian container
```

As you can see the two containers work together in this scenario with the help of the volume. This is a simple example,
but complex scenarios can be built on the presented concepts.

Go back to the student machine and delete the pods:

```bash
# exit back to student machine
exit
```

```bash
# on student machine
kubectl delete svc two-containers-svc
kubectl delete pod two-containers
```

## 4.2 ConfigMaps

`ConfigMaps` allow developers to decouple configuration options from the app source code or container image.

![roles](assets/config_map.png)

There are four different ways that you can use a ConfigMap to configure a container inside a Pod:
 * Inside a container command and args
 * Environment variables for a container
 * Add a file in read-only volume, for the application to read
 * Write code to run inside the Pod that uses the Kubernetes API to read a ConfigMap

When a `ConfigMap` currently consumed in a volume is updated, projected keys are eventually updated as well. The kubelet checks whether
the mounted `ConfigMap` is fresh on every periodic sync.
`ConfigMaps` consumed as environment variables are not updated automatically and require a pod restart.

**NOTE**: `ConfigMap` does not provide secrecy or encryption. If the data you want to store is confidential, use a `Secret`
rather than a `ConfigMap`, or use additional (third party) tools to keep your data private.

Create a `ConfigMap` with literal values:

```bash
kubectl create configmap test-configmap --from-literal=val1=dan \
--from-literal=val2=bill --from-literal=val3=ben
```

Inspect the `ConfigMap`:

```bash
kubectl describe configmap test-configmap

# output
Name:         test-configmap
Namespace:    default
Labels:       <none>
Annotations:  <none>

Data
====
val1:
----
dan
val2:
----
bill
val3:
----
ben
Events:  <none>
```

Create a Pod that references the `ConfigMap`.

```bash
apiVersion: v1
kind: Pod
metadata:
  name: configmap-pod
spec:
  containers:
  - name: pod-with-configmap
    image: alpine
    command: ["sleep", "999999"]
    envFrom:
    - prefix: CONFIG_DATA_
      configMapRef:
        name: test-configmap
```

```bash
kubectl create -f ~/resources/pod-with-configmap.yaml
```

Check if the Pod sees the values:

```bash
kubectl exec configmap-pod -- env | grep CONFIG_DATA

# output
...
CONFIG_DATA_val1=dan
CONFIG_DATA_val2=bill
CONFIG_DATA_val3=ben
...
```

Delete the pod:

```bash
kubectl delete pod configmap-pod
```

For more information on `ConfigMaps`, please visit:

https://kubernetes.io/docs/concepts/configuration/configmap/



## 4.3 Secrets

`Secrets` are a way to securely inject sensitive data into Pods. By sensitive data is meant: credentials, encryption keys,
tokens, etc. The data is represented as key-values pairs and are encoded in base64.

There are two ways to create secrets, from CLI using `kubectl` or from a file definition, we'll use the CLI method:

```bash
kubectl create secret generic bob-secret --from-literal=username='bob' \
--from-literal=password='Passw0rd'
```

**NOTE**: If the CLI method is used, the values will automatically be encoded for the user. If the file definition is used,
the user will have to input the already encoded values in the definition.

Observe the secret and node the encoded value:

```bash
kubectl get secret bob-secret

# output
NAME         TYPE     DATA   AGE
bob-secret   Opaque   2      10s
```

`type: Opaque` means that contents of this Secret is unstructured, it can contain arbitrary key-value pairs.
Other types of secrets can be `service-account-token`, `dockercfg`, `dockerconfigjson`, `ssh-auth`, `tls`.
For more info on Secret types please visit:

https://kubernetes.io/docs/concepts/configuration/secret/#secret-types

```bash
kubectl describe secret bob-secret

# output
Name:         bob-secret
Namespace:    default
Labels:       <none>
Annotations:  <none>

Type:  Opaque

Data
====
password:  8 bytes
username:  3 bytes
```

```bash
kubectl get secret bob-secret -o yaml
```

Now create a pod that has access to the `Secret` via environment variables. Here is the pod definition `~/resources/pod-with-secrets.yaml`:

```bash
cat ~/resources/pod-with-secrets.yaml

# output
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-secrets
spec:
  containers:
  - name: container-with-secrets
    image: nginx
    env:
    - name: SECRET_USERNAME
      valueFrom:
        secretKeyRef:
          name: bob-secret
          key: username
    - name: SECRET_PASSWORD
      valueFrom:
        secretKeyRef:
          name: bob-secret
          key: password
```

Create the pod:

```bash
kubectl create -f ~/resources/pod-with-secrets.yaml
```

Wait for the pod to come up. Connect to it afterwards and see if the secrets were passed:

```bash
kubectl exec -it pod-with-secrets -- /bin/bash
```

```bash
root@pod-with-secrets:/# printenv | grep SECRET

# output
SECRET_PASSWORD=Passw0rd
SECRET_USERNAME=bob
```

Now, a database, for example, can directly reference the environment variables for credentials.

Exit the pod and delete the resources you've created:

```bash
root@pod-with-secrets:/# exit
```

```bash
kubectl delete pod pod-with-secrets
kubectl delete secret bob-secret
```


## 4.4 PersistentVolumes, PersistentVolumeClaims and StorageClasses

This works great but volume types such as `emptyDir` and `hostPath` have the drawback that developers need to have knowledge of
the storage and network infrastructure. Storage should be provisioned in a transparent manner and fully abstracted of the backend solution.

`PersistentVolumes`, `PersistentVolumeClaims` and `StorageClasses` can be used. A storage backend is represented by
the `StorageClass`. It dynamically provisions `PVs` with the help of `PVCs`.

**NOTE**: PersistentVolumes will be referenced with `PVs`, `PersistentVolumeClaims` with `PVCs` and `StorageClasses`
with `SCs`.

`PVs` are like volumes, but it's lifecycle does not depend on the pods lifecycle. A user or pod can request a `PV` with a `PVC`.

![roles](assets/pvc.png)

Administrators can also create `PVs` statically, meaning that the PVs will pe pre-provisioned. This is bad because it's not automated, and may require manual(
intervention later on. `SCs` are allow for `PVs` to be provisioned dynamically.

Your cluster is using `hostPath` storage. To get the current configured (and `default`) storage class:

```bash
kubectl get sc

# output
NAME                            PROVISIONER              RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
csi-rawfile-default (default)   rawfile.csi.openebs.io   Delete          WaitForFirstConsumer   true                   48m
```

Also, you can get details about your storage class:

```bash
kubectl describe sc csi-rawfile-default

# output
Name:                  csi-rawfile-default
IsDefaultClass:        Yes
Annotations:           meta.helm.sh/release-name=ck-storage,meta.helm.sh/release-namespace=kube-system,storageclass.kubernetes.io/is-default-class=true
Provisioner:           rawfile.csi.openebs.io
Parameters:            <none>
AllowVolumeExpansion:  True
MountOptions:          <none>
ReclaimPolicy:         Delete
VolumeBindingMode:     WaitForFirstConsumer
Events:                <none>
```

For more info on storage classes please visit:

https://kubernetes.io/docs/concepts/storage/storage-classes/

https://documentation.ubuntu.com/canonical-kubernetes/latest/snap/howto/storage/

Great now we can dynamically allocate volumes for containers, the way workflows are intended to be.

Create a `PVC` using the `SC` from `~/resources/gce-pvc.yaml`:

```bash
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: hostpath-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: csi-rawfile-default
```

`PVCs` are the way to bind to `PVs`. Create the `PVC`:

```bash
kubectl create -f ~/resources/hostpath-pvc.yaml
```

```bash
kubectl get pvc

# output
NAME           STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS          VOLUMEATTRIBUTESCLASS   AGE
hostpath-pvc   Pending                                      csi-rawfile-default   <unset>                 10s
```

```bash
kubectl describe pvc hostpath-pvc

# output
Name:          hostpath-pvc
Namespace:     default
StorageClass:  csi-rawfile-default
Status:        Pending
Volume:
Labels:        <none>
Annotations:   <none>
Finalizers:    [kubernetes.io/pvc-protection]
Capacity:
Access Modes:
VolumeMode:    Filesystem
Used By:       <none>
Events:
  Type    Reason                Age               From                         Message
  ----    ------                ----              ----                         -------
  Normal  WaitForFirstConsumer  5s (x4 over 40s)  persistentvolume-controller  waiting for first consumer to be created before binding
```

The `PVC` is bound to a `Persistent Volume`.

```bash
kubectl get pv

# output
No resources found
```

The volume will be created upon pod creation.

Create a pod that will make use of the new `PV` with `~/resources/busybox-with-pv.yaml`:

```bash
apiVersion: v1
kind: Pod
metadata:
  name: busybox
  namespace: default
spec:
  containers:
    - image: busybox
      command:
        - sleep
        - "3600"
      imagePullPolicy: IfNotPresent
      name: busybox
      volumeMounts:
        - mountPath: "/pv"
          name: testvolume
  restartPolicy: Always
  volumes:
    - name: testvolume
      persistentVolumeClaim:
        claimName: hostpath-pvc
```

```bash
kubectl create -f ~/resources/busybox-with-pv.yaml
```

After the pod gets created, let's check again the PersistentVolumeClaim status:

```bash
kubectl get pvc

# output
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS          VOLUMEATTRIBUTESCLASS   AGE
hostpath-pvc   Bound    pvc-885f7ff8-8dbc-4f00-bd56-f92edbfa2e3c   10Gi       RWO            csi-rawfile-default   <unset>                 3m37s
```

Check inside the pod to see if the volume was mounted:

```bash
kubectl exec busybox -- mount | grep pv

# output
/dev/loop3 on /pv type ext4 (rw,relatime)
```

If the new device shows up, we have successfully configured and provisioned an hostPath-backed PV.

Let's write some data on the PV. Create a file called `hello-world.txt`.

```bash
kubectl exec busybox --  touch /pv/hello-world.txt
```

Connect to the pod and write some text in the file.

```bash
kubectl exec -it busybox -- sh
```

```bash
echo "Hello world from busybox pod!" > /pv/hello-world.txt
```

```bash
cat /pv/hello-world.txt

# output
Hello world from busybox pod!
```

Exit the pods and delete it. Let's see if the `PV` and data will be persistent.

```bash
exit
```

```bash
kubectl delete pod busybox
```

Create a new pod but use the same `PVC`.

```bash
kubectl create -f ~/resources/nginx-with-pv.yaml
```

Connect to the pod to see of the data is still there.

```bash
kubectl exec -it nginx -- sh
```

```bash
ls /pv/hello-world.txt
```

```bash
cat /pv/hello-world.txt

# output
Hello world from busybox pod!
```

All is order. Now we can exit and delete the pod.

```bash
exit
```

Dynamically allocated PVs is the most flexible and reliable way to allocate storage for applications running in Kubernetes.
Cleanup the pods we've created in this chapter:

```bash
kubectl delete pod nginx
kubectl delete pvc hostpath-pvc
```


# 5. Autoscaling !heading

Kubernetes can autoscale your application based on load. Numeric based resources like `CPU` and `Memory` can be used for this.
For example, when the CPU reaches a certain threshold, the application can be scaled without human interaction, in an automated manner.

The `HorizontalPodAutoscaler` normally fetches metrics from a series of aggregated APIs (metrics.k8s.io, custom.metrics.k8s.io,
and external.metrics.k8s.io). The `metrics.k8s.io` API is usually provided by `metrics-server`, which needs to be launched separately.

![roles](assets/hpa1.png)

Resource usage metrics, such as container CPU and memory usage, are available in Kubernetes through the `Metrics API`. These metrics can be
accessed either directly by the user with the `kubectl top` command, or by a controller in the cluster, for example `HorizontalPodAutoscaler`,
to make decisions. Provided by the `metrics-server`.

`Metrics Server` collects resource metrics from Kubelets and exposes them in Kubernetes API Server through `Metrics API` for use by
`Horizontal Pod Autoscaler` and `VerticalPodAutoscaler`. Metrics Server is not meant for non-autoscaling purposes. For example, don't
use it to forward metrics to monitoring solutions, or as a source of monitoring solution metrics. For this Prometheus can be used.

The `HorizontalPodAutoscaler` is the Kubernetes object that scales a `Deployment` or `ReplicaSet`. It is a control loop that periodically
checks pod metrics from the `metrics-server`, calculates the number of replicas required to meet the target metric value configured by the user in
the `HPA` resource, and updates the `REPLICAS` field in the target Deployment resource.

So the autoscaling process works in 3 steps:
  * collect metrics from all the pods managed by the resource object (deployment, replicaSet) : via `metrics-server`
  * calculate the number of pods needed to match the specified target value
  * update the replicas field in the resource object


![roles](assets/hpa2.png)


More information on the Resource metrics pipeline can be found here:

https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/


## 5.1 Autoscale a Deployment resource

Create an nginx deployment, this will be the scaled application:

```bash
kubectl create deployment nginx-hpa --image=nginx
```

```bash
kubectl expose deployment nginx-hpa --port=80
```

```bash
kubectl set resources deployment nginx-hpa --requests=cpu=100m
```

Create a `HPA` that will autoscale when the pod `CPU` load reaches 30%, but keep the pods between 1 pod minimum and 5 pods
at max. In this case the pod replicas will not exeed 5 even if the `CPU` is above 30%:

```bash
kubectl autoscale deployment nginx-hpa --cpu 30% --min=1 --max=5
```

Run a load generator that will do `wget` continuously on the nginx app:

```bash
kubectl run -i --tty load-generator --image=busybox /bin/sh
```

```bash
# inside loadgenerator container
while true; do wget -q -O- http://nginx-hpa; done
```

Open a new tab and log in the public machine again. Do a watch getting the `HPA` status. Wait a minute or two for the load to increase:

```bash
watch kubectl get hpa
NAME        REFERENCE              TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
nginx-hpa   Deployment/nginx-hpa   36%/30%   1         5         2          4m
```

Because the CPU utilization went over 30%, it's 36% now, a new replica was added and there are 2 now. Please note that in your case the
load can be higher, and the replica count can be higher.

A new nginx pod was added and the app was autoscaled:

```bash
kubectl get pods

# output
NAME                        READY   STATUS    RESTARTS   AGE
load-generator              1/1     Running   0          2m12s
nginx-hpa-998cbd759-2zzng   1/1     Running   0          3m14s
nginx-hpa-998cbd759-gsxbl   1/1     Running   0          82s
nginx-hpa-998cbd759-rjs8n   1/1     Running   0          82s
...
```

If you go back on the first tab and stop the `wget` command, the CPU utilization will drop below 30% and the `REPLICAS` field will be set to 1.
The scale down operation is performed every five minutes, so you may not see this right away.

```bash
kubectl get hpa

# output
NAME        REFERENCE              TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
nginx-hpa   Deployment/nginx-hpa   cpu: 0%/30%   1         5         1          10m
```

Inspect the `HPA` for a minute, if you find something interesting don't hesitate to talk with the trainer about it:

```bash
kubectl describe hpa nginx-hpa
```

You can check what happened to the HorizontalPodAutoscaler using:

```bash
kubectl events --for hpa/nginx-hpa

# output
LAST SEEN   TYPE      REASON                         OBJECT                              MESSAGE
9m23s       Normal    SuccessfulRescale              HorizontalPodAutoscaler/nginx-hpa   New size: 3; reason: cpu resource utilization (percentage of request) above target
2m8s        Normal    SuccessfulRescale              HorizontalPodAutoscaler/nginx-hpa   New size: 2; reason: All metrics below target
113s        Normal    SuccessfulRescale              HorizontalPodAutoscaler/nginx-hpa   New size: 1; reason: All metrics below target
```

Default behavior of the `HorizontalPodAutoscaler` is desribed here:

```bash
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
    - type: Percent
      value: 100
      periodSeconds: 15
  scaleUp:
    stabilizationWindowSeconds: 0
    policies:
    - type: Percent
      value: 100
      periodSeconds: 15
    - type: Pods
      value: 4
      periodSeconds: 15
    selectPolicy: Max
```

Do a cleanup on the created resources:

```bash
kubectl delete deploy nginx-hpa
kubectl delete svc nginx-hpa
kubectl delete pod load-generator
kubectl delete hpa nginx-hpa
```

For more information on HPAs, please visit:

https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/
https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/


# 6. Authentication and Authorization !heading

## 6.1 Users and ServiceAccounts

Kubernetes does NOT have a resource called `user`. It has the concept of `ServiceAccounts` which live inside `Namespaces`,
objects used for multi-tenancy. However, Kubernetes understands the concept of users as an external object.

`ServiceAccounts` are Kubernetes resource types that are associated with Pods to offer them the possibility to talk to the
API Server. They represent the identify of the app running inside Pods. Pods can make API calls against the Server to request
pod metadata such as: pod name, IP, namespace, labels, CPU and memory utilization. Usually, apps can make use of this kind of
information. Each `SA` contains a token, this token is mounted as a `secret` volume inside pods on creation. The token is then used
to authenticate and authorize the pod requests for the API Server.

Kubernetes distinguishes between the concept of a user account and a service account for a number of reasons:
  * user accounts are for humans, the intent is for user accounts to be managed externally to the Kubernetes cluster
  * service accounts are for Pods and processes that run in them
  * user accounts are global and unique across all namespaces of the cluster
  * service accounts are namespaced
  * auditing for humans and service accounts may differ

Each namespace has a `default` `SA`. Additional `SAs` can be created for security reasons, read-only `SAs` for pods
that only need to read API info, and separate `SAs` with write permissions for pods that need to modify API objects.

Each Pod is associated with a `SA` on creation. If no `SA` is specified in the Pod definition, the namespace default `SA`
is used. The `secret` volume contains the `default` token of the namespace in which the pod is running.

In this chapter we'll create a pod with `curl` binary installed and see how the secret volume is mounted in it. The last step would
be to send an API request to the API server.

First, let's check the default namespace and the `SAs`:

```bash
kubectl get namespace

# output
NAME              STATUS   AGE
cilium-secrets    Active   25h
default           Active   25h
kube-node-lease   Active   25h
kube-public       Active   25h
kube-system       Active   25h
metallb-system    Active   25h
```

Get the default namespace `SA`:

```bash
kubectl get sa
# output
# as mentioned, each Namespace has a default ServiceAccount within it.
NAME      SECRETS   AGE
default   0         25h
```

Get the `SA` for all the namespaces:

```bash
kubectl get sa --all-namespaces
```

Inspect the default namespace `SA`:

```bash
kubectl describe sa default

# output
Name:                default
Namespace:           default
Labels:              <none>
Annotations:         <none>
Image pull secrets:  <none>
Mountable secrets:   <none>
Tokens:              <none>
Events:              <none>
```

Since Kubernetes v1.24 there are no tokens generated for service accounts by default. A `Secret` definition for the default service account looks like this:

```bash
cat ~/resources/service-account-token.yaml

# output
apiVersion: v1
kind: Secret
metadata:
  name: default-serviceaccount-secret
  annotations:
    kubernetes.io/service-account.name: default
type: kubernetes.io/service-account-token
```


To generate one, please run:

```bash
kubectl create -f ~/resources/service-account-token.yaml
```

To get details about the generated ServiceAccount secret, run:

```bash
kubectl describe secret default-serviceaccount-secret

# output
Name:         default-serviceaccount-secret
Namespace:    default
Labels:       <none>
Annotations:  kubernetes.io/service-account.name: default
              kubernetes.io/service-account.uid: a0c53e14-fd50-476c-a085-b013256ccf3c

Type:  kubernetes.io/service-account-token

Data
====
ca.crt:     1139 bytes
namespace:  7 bytes
token:      eyJhbGciOiJSUzI1NiIsImtpZCI6Ik....
```

Now create the `alpine` pod and see if the token is mounted:

```bash
kubectl create -f ~/resources/curl-pod.yaml
```

```bash
kubectl describe pod curl

# output
...
Volumes:
  kube-api-access-7qjdk:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
...
```

Kubernetes mounts the secret volume at `/var/run/secrets/kubernetes.io/serviceaccount/` inside the container. Based on the
certificate and token, the application can talk to the API Server when needed:

```bash
kubectl exec -it curl -- sh
```

```bash
ls -l /var/run/secrets/kubernetes.io/serviceaccount/

# output
lrwxrwxrwx    1 root     root            13 Jul 25 17:35 ca.crt -> ..data/ca.crt
lrwxrwxrwx    1 root     root            16 Jul 25 17:35 namespace -> ..data/namespace
lrwxrwxrwx    1 root     root            12 Jul 25 17:35 token -> ..data/token
```

Install `curl` inside the container:

```bash
apk add curl
```

Note that you can get the API cluster IP with `kubectl get svc` or the DNS record which is `kubernetes`.

```bash
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
-H "Authorization: Bearer $TOKEN" https://kubernetes/api

curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
-H "Authorization: Bearer $TOKEN" https://kubernetes/api/v1
```

A long list of API should be listed and the available verbs for those APIs. If we would have not used the certificate and token, this request would have NOT been unauthorized.

**NOTE**: `ServiceAccounts` must be set when creating the pod. It can't be changed later. One pod is associated with only one `SA`, but
multiple pods can use the same `SA` in a namespace.

Get back to the host.

```bash
exit
```

Cleanup the pod:

```bash
kubectl delete pod curl
```

## 6.2 RBAC, Roles and ClusterRoles

All Kubernetes resources are objects which allow CRUD (create, read, update, delete) operations. Role-based access control (RBAC)
is a method of regulating access to resources based on the roles of individual users. RBAC works and understands 4 types of
Kubernetes resources:
  * `Role` and `ClusterRole`: contain rules that represent a set of permissions. Permissions are additive, no `deny` rules. `Roles` grant access to resources within a single namespace, while `ClusterRoles` are cluster-wide.
  * `RoleBinding` and `ClusterRoleBinding`: grant permissions defined in a `Role` to a user or set of users

![roles](assets/roles_bindings.png)


By default, Canonical Kubernetes comes with `RBAC` enabled. You can verify this by checking the authorization mode:

```bash
juju ssh k8s/0 -- "ps aux | grep kube-apiserver"

# output
...
--authorization-mode=Node,RBAC
...
```

Users can create their own `Roles` and `ClusterRoles` - see the definitions, but Kubernetes clusters also come with a default set of `ClusterRoles`.
The “edit” role lets users perform basic actions like deploying pods; “view” lets a user observe non-sensitive resources; “admin”
allows a user to administer a namespace; and “cluster-admin” grants access to administer a cluster. Take a look:

```bash
kubectl get clusterroles
```

### Create a ServiceAccount and grant permissions

In this exercise we'll create a `ServiceAccount`, a `Role` and a `RoleBinding`. The `Role` will grant
read access to pod resources in the default namespace.

The `SA` definition looks like this in `~/resources/student-sa.yaml`:

```bash
cat ~/resources/student-sa.yaml

# output
apiVersion: v1
kind: ServiceAccount
metadata:
 name: student-sa
 namespace: default
```

Create the `SA`:

```bash
kubectl create -f ~/resources/student-sa.yaml
```

The `Role` definition looks like this in `~/resources/pod-reader-role.yaml`:

```bash
cat ~/resources/pod-reader-role.yaml

# output
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

Create the `Role`:

```bash
kubectl create -f ~/resources/pod-reader-role.yaml
```

The `Role` has to be associated with the user, this is done with the `RoleBinding` resource in `~/resources/pod-reader-rb.yaml`:

```bash
cat ~/resources/pod-reader-rb.yaml

# output
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: ServiceAccount
  name: student-sa
roleRef:
  kind: Role #this must be Role or ClusterRole
  name: pod-reader # this must match the name of the Role or ClusterRole you wish to bind to
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl create -f ~/resources/pod-reader-rb.yaml
```

Inspect the `RoleBinding`, it should be associated with `student-sa`:

```bash
kubectl describe rolebinding read-pods

# output
Name:         read-pods
Labels:       <none>
Annotations:  <none>
Role:
  Kind:  Role
  Name:  pod-reader
Subjects:
  Kind            Name        Namespace
  ----            ----        ---------
  ServiceAccount  student-sa
```

Create a Pod with the newly created `SA`. The pod definition looks like this in `~/resources/curl-pod-with-sa.yaml`:

```bash
cat ~/resources/curl-pod-with-sa.yaml

# output
apiVersion: v1
kind: Pod
metadata:
  name: curl
spec:
  serviceAccountName: student-sa
  containers:
  - name: curl
    image: alpine
    command: ["sleep", "999999"]
```

The key field here is `serviceAccountName: student-sa`. Create the Pod:

```bash
kubectl create -f ~/resources/curl-pod-with-sa.yaml
```

Finally, start a bash process inside the container and attach to it.

```bash
kubectl exec -it curl -- sh
```

Install `curl` inside the container:

```bash
apk add curl
```

Query the API server for pods, this action should be allowed:

```bash
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
-H "Authorization: Bearer $TOKEN" https://kubernetes/api/v1/namespaces/default/pods

# output
{
  "kind": "PodList",
  "apiVersion": "v1",
  "metadata": {
    "resourceVersion": "98947"
  },
  "items": [
    {
      "metadata": {
        "name": "curl",
        "namespace": "default",
        "uid": "aed4abe5-490b-477b-a100-cec137cceb9f",
        "resourceVersion": "98907",
        "generation": 1,
        "creationTimestamp": "2026-03-19T10:50:58Z",
        "managedFields": [
          {
            "manager": "kubectl-create",
            "operation": "Update",
            "apiVersion": "v1",
            "time": "2026-03-19T10:50:58Z",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:spec": {
                "f:containers": {
                  "k:{\"name\":\"curl\"}": {
                    ".": {},
                    "f:command": {},
                    "f:image": {},
                    "f:imagePullPolicy": {},
                    "f:name": {},
                    "f:resources": {},
                    "f:terminationMessagePath": {},
                    "f:terminationMessagePolicy": {}
                  }
...
```

Now let's try to read something we should not be allowed to see, like `Secrets`:

```bash
curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
-H "Authorization: Bearer $TOKEN" https://kubernetes/api/v1/namespaces/default/secrets

# output
{
  "kind": "Status",
  "apiVersion": "v1",
  "metadata": {},
  "status": "Failure",
  "message": "secrets is forbidden: User \"system:serviceaccount:default:student-sa\" cannot list resource \"secrets\" in API group \"\" in the namespace \"default\"",
  "reason": "Forbidden",
  "details": {
    "kind": "secrets"
  },
  "code": 403
}
```

As expected, forbidden action.

Get back to the student host:

```bash
exit
```

Cleanup:

```bash
kubectl delete pod curl
kubectl delete rolebinding read-pods
kubectl delete role pod-reader
kubectl delete sa student-sa
```


# 7. Helm !heading

Helm is like a package manager for Kubernetes. It allows users to install simple or complex apps with `Charts`. Charts
are packages of pre-configured Kubernetes resources.

In this chapter we'll install a `wordpress` stack with a `mariaDB` database. This requires some Kubernetes resources such as:
pods, loadBalancer services, `PVCs` and `PVs`. All of this will be deployed from a chart.


## 7.1 Deploy an app

Install helm client on the student machine:

```bash
sudo snap install helm --channel=latest/stable --classic
```

Once you have Helm ready, you can add a chart repository. One popular starting location is the official Helm stable charts:

```bash
helm repo add stable https://charts.helm.sh/stable
```

```bash
helm repo list
```

Update the information of available charts locally from chart repositories:

```bash
helm repo update
```

List the charts you can install from the stable repo:

```bash
helm search repo stable
```

Search for the individual `Wordpress` chart:

```bash
helm search repo stable/wordpress
```

The Wordpress chart from this repo is deprecated. We will install Wordpress from another repo. Add the `Bitnami` repo:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

Search the new repo for the Wordpress chart:

```bash
helm search repo bitnami/wordpress
```

Inspect the chart:

```bash
helm show chart bitnami/wordpress
```

Get all the information of the chart:

```bash
helm show all bitnami/wordpress
```

Or, list only the variables of the chart:

```bash
helm show values bitnami/wordpress
```

Those variables can be overridden on deploy time either by using `--set` (we will use this method for install), or by using a
YAML formatted file with the changed variables, e.g. `helm install -f config.yaml stable/wordpress`. More information on this
can be found here:

https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing


Here is a link to the Git repo of the chart. More information on installation and supported config options can be inspected:

https://github.com/bitnami/charts/tree/master/bitnami/wordpress/#installing-the-chart

Time to install the chart:

```bash
helm install my-wordpress-blog \
  --set wordpressUsername=admin \
  --set wordpressPassword=password \
  --set mariadb.auth.rootPassword=secretpassword \
    bitnami/wordpress
```

**NOTE**: if the `mariadb.auth.rootPassword` variable is not set, the `mariadb` pod will fail to start due to failing liveness probes

The installation output will show lots of useful information, like how to access the chart application and how to get
credentials for the app. This information can also be accessed with the `status` command:

```bash
helm status my-wordpress-blog
```

List the installed charts:

```bash
helm list
```

List the pods:

```bash
kubectl get pods

# output
NAME                                READY   STATUS    RESTARTS   AGE
my-wordpress-blog-fc4665457-hb8jr   1/1     Running   0          91s
my-wordpress-blog-mariadb-0         1/1     Running   0          91s
```

The chart created a loadBalancer service:

```bash
kubectl get svc

# output
NAME                                 TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)                      AGE
kubernetes                           ClusterIP      10.152.183.1     <none>          443/TCP                      26h
my-wordpress-blog                    LoadBalancer   10.152.183.62    10.237.75.129   80:31834/TCP,443:30894/TCP   119s
my-wordpress-blog-mariadb            ClusterIP      10.152.183.159   <none>          3306/TCP                     119s
my-wordpress-blog-mariadb-headless   ClusterIP      None             <none>          3306/TCP                     119s
```

Now the wordpress app should be available via `10.237.75.129`.

In this chapter we saw how easy it is to deploy simple or complex apps with Helm.

## 7.2 Deployment Chart

First, the application code has to be built into a Docker image. Here you can find code for a simple `nodejs` web app plus
the `Dockerfile` for it:

https://github.com/cloudbase/kubernetes-tools

```bash
cd ~ && git clone https://github.com/cloudbase/kubernetes-tools.git
```

There are two ways to get the image, either build it or pull it from `DockerHub`. I am going to demonstrate how to built it, you don't
have to do it because the image is going to be pulled from `DockerHub`.

**NOTE**: do not run the commands in the following box, only for demonstration, the images are already on DockerHub. You
can skip the next few commands until you see "Demonstration ends here".

<em>
```bash
# only for demonstration
cd ~/kubernetes-tools/web-app/
docker build -t <username>/web-app .
docker tag <username>/web-app <username>/web-app:v1
```
</em>

The image is already public on `DockerHub`. It will automatically get pulled on all Kubernetes Nodes upon Pod creation.

Because the image is used with a complex environment like Kubernetes, it's useful to test it beforehand on it's own:

<em>
```bash
docker run -p 80:80 <username>/web-app:v1
```
</em>

Open another tab on your public machine and test the container:

<em>
```bash
curl localhost:80
```
</em>

Go back on the first tab and kill the container with `CTRL+C`.

**NOTE**: Demonstration ends here.

Create a helm chart template and modify `values.yaml` to point to the correct image (`repository` and `tag`) and `replicaCount`:

```bash
helm create ~/web-app; cd ~/web-app
```

```bash
vim values.yaml
# do desired edits on values.yaml, for example specify
# <username>/web-app:v1 Docker image

...
replicaCount: 3

image:
  repository: pvradu/web-app
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "v1"
...
```

Package the app:

```bash
helm package .
```

Dry install the chart:

```bash
# do a dry run to check that everything is ok
helm install --debug --dry-run web-app-0.1.0.tgz --generate-name
```

Install it:

```bash
helm install web-app-stateless web-app-0.1.0.tgz
```

More info on Helm templating:
https://docs.helm.sh/chart_template_guide/

Verify the pod is running:

```bash
kubectl get pods

# output
NAME                                 READY   STATUS    RESTARTS   AGE
web-app-stateless-5bd5fffc48-654wt   1/1     Running   0          62s
web-app-stateless-5bd5fffc48-qrmkh   1/1     Running   0          62s
web-app-stateless-5bd5fffc48-xwcnq   1/1     Running   0          62s
```

Also verify there's a service created:

```bash
kubectl get svc web-app-stateless

# output
NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
web-app-stateless   ClusterIP   10.152.183.20   <none>        80/TCP    88s
```

Because the app now has a ClusterIP service, you can go on any of the Nodes and do a curl on it on port `80`.
Connect to the node `0` and do a few `curl` commands on the ClusterIP of the chart. What happends?

```bash
juju ssh 0 -- curl -s 10.152.183.20

# output
This app is running in pod web-app-stateless-5bd5fffc48-xwcnq

### try again
juju ssh 0 -- curl -s 10.152.183.20

# output
This app is running in pod web-app-stateless-5bd5fffc48-654wt

### try one more time
juju ssh 0 -- curl -s 10.152.183.20

# output
This app is running in pod web-app-stateless-5bd5fffc48-qrmkh
```
Delete the application:

```bash
helm delete web-app-stateless
```

## 7.3 StatefulSet Chart

The Docker image can be built as before. I will only demonstrate how to do this, the image is already public so no need for you
to to this:

**NOTE**: do not run the commands in the following box, only for demonstration, the images are already on DockerHub. You
can skip the next few commands until you see "Demonstration ends here".

<em>
```bash
# only for demonstration
cd ~/kubernetes-tools/web-app-stateful/image
docker build -t <username>/web-app-stateful .
docker tag <username>/web-app-stateful <username>/web-app-stateful:v1
```
</em>
**NOTE**: Demonstration ends here.

The image is already public on `DockerHub`. It will automatically get pulled on all Kubernetes Nodes upon Pod creation.

Build the Chart:


```bash
mkdir ~/web-app-stateful && cd ~/web-app-stateful
cp -r ~/kubernetes-tools/web-app-stateful/chart/* ~/web-app-stateful/
```

Package the app:

```bash
helm package .
```

Based on the archive that we now have, we can install the Helm chart anywhere:

```bash
helm install web-app-stateful web-app-stateful-0.1.0.tgz
```

The `StatefulSet` requires a `clusterIP` headless service, this means that the service will not have an IP. So how do we connect to the
app? There are two ways, create another `clusterIP` service or use the proxy. On the student host run the proxy service:

```bash
kubectl proxy

# output
Starting to serve on 127.0.0.1:8001
```

Open another terminal tab on your student machine. List your apps to get the name of the `StatefulSet` and query the pods:

```bash
helm list

# output
web-app-stateful
```

Verify helm installed a StatefulSet and check the pods:

```bash
kubectl get statefulsets.apps

# output
NAME               READY   AGE
web-app-stateful   2/2     2m32s
```

```bash
kubectl get pods

# output
NAME                 READY   STATUS    RESTARTS   AGE
web-app-stateful-0   1/1     Running   0          100s
web-app-stateful-1   1/1     Running   0          95s
```

```bash
curl localhost:8001/api/v1/namespaces/default/pods/web-app-stateful-0/proxy/

# output
You hit web-app-stateful-0
Data stored on this pod: No data posted yet
```

```bash
curl localhost:8001/api/v1/namespaces/default/pods/web-app-stateful-1/proxy/

# output
You hit web-app-stateful-1
Data stored on this pod: No data posted yet
```

No persistent data in the pods yet -> `Data stored on this pod: No data posted yet`.

Write data to a pod and check to see if it was written:

```bash
curl -X POST -d "Hey there!" \
localhost:8001/api/v1/namespaces/default/pods/web-app-stateful-1/proxy/

# output
Data stored on pod web-app-stateful-1
```

```bash
curl localhost:8001/api/v1/namespaces/default/pods/web-app-stateful-1/proxy/

# output
You hit web-app-stateful-1
Data stored on this pod: Hey there!
```

Indeed, data was written -> `Data stored on this pod: Hey there!`.

Delete the pod that stores the data:

```bash
kubectl delete pod web-app-stateful-1
```

Right after the delete, list the pods to see when happened:

```bash
kubectl get pods

# output
NAME                 READY   STATUS    RESTARTS   AGE
web-app-stateful-0   1/1     Running   0          4m14s
web-app-stateful-1   1/1     Running   0          8s
```

There is a new pod but with the same name as the one deleted, we know this because it's only `8s` old.

The pod should be recreated by the `StatefulSet` but should retain the stored information:

```bash
curl localhost:8001/api/v1/namespaces/default/pods/web-app-stateful-1/proxy/

# output
You hit web-app-stateful-1
Data stored on this pod: Hey there!
```

Indeed, the data persisted -> `Data stored on this pod: Hey there!`

Data persisted also because the pods were using a PV/PVC:

```bash
kubectl get pv
kubectl get pvc
```

Do a cleanup:

```bash
helm delete web-app-stateful
```

# 7.4 Headlamp

Headlamp is a user-friendly Kubernetes UI focused on extensibility. Headlamp was created to blend the traditional feature set of other web UIs/dashboards (i.e., to list and view resources) with added functionality. A common use case for any Kubernetes web UI is to deploy it `in-cluster` and set up an `ingress server` for having it available to users. We're going to do an `in-cluster` deployment.

First, let's add the Headlamp chart repository:

```bash
helm repo add headlamp https://kubernetes-sigs.github.io/headlamp/
```

Update the repository:

```bash
helm repo update
```

Search for the Headlamp chart:

```bash
helm search repo headlamp
```

Install Headlamp:

```bash
helm install headlamp headlamp/headlamp --namespace kube-system \
  --set replicaCount=3 \
  --set service.type=LoadBalancer
```

As of chart version 0.40.1, there’s a known bug where the Helm chart passes a -session-ttl flag that the binary doesn't recognize. The pod will CrashLoopBackOff. Fix it by running:

```bash
kubectl get deploy headlamp -n kube-system -o json | \
  jq '.spec.template.spec.containers[0].args |= map(select(. != "-session-ttl=86400"))' | \
  kubectl apply -f -
```

If the chart version is greater than 0.40.1, this step may not be needed.
Check the status of the installation:

```bash
helm status headlamp -n kube-system
```

Check the pods:

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=headlamp

# output
NAME                        READY   STATUS    RESTARTS   AGE
headlamp-7975f584c8-2j69s   1/1     Running   0          11m
headlamp-7975f584c8-62vvr   1/1     Running   0          11m
headlamp-7975f584c8-rtvng   1/1     Running   0          11m
```

Check the `LoadBalancer` service created:

```bash
kubectl get services -n kube-system -l app.kubernetes.io/name=headlamp

# output
NAME       TYPE           CLUSTER-IP       EXTERNAL-IP      PORT(S)        AGE
headlamp   LoadBalancer   10.152.183.231   10.237.75.130   80:32126/TCP   11m
```

Headlamp will create a `ServiceAccount` once it is installed called `headlamp` in your `kube-system` namespace. You can create a token for the `ServiceAccount` by running:

```bash
kubectl create token headlamp --namespace kube-system

# output
eyJhbGciOiJSUzI1NiIsImtpZCI6Ik1...
```

You can now use this token to authenticate to Headlamp. Open a tunneled browser session to `http://10.237.75.130` (Loadbalancer IP). You will be asked for a token to authenticate.


# 8. Upgrading Canonical Kubernetes !heading

The installed version of Kubernetes is `1.34`, which is not the latest one. In this chapter we will learn how easy
it is to upgrade the Canonical Kubernetes cluster to a newer `1.35` version with in place upgrades. This is another powerful
Juju feature. Charms are written in such a way that upgrading and scaling are easy to do.

Before upgrading the cluster, you should also make sure:
* the machine from which you will perform the backup has sufficient internet access to retrieve updated software
* your cluster is running normally
* you read the Upgrade notes to see if any caveats apply to the versions you are upgrading to/from
* you read the Release notes for the version you are upgrading to, which will alert you to any important changes to the operation of your cluster


## 8.1 Upgrade Kubernetes

Check the current cluster status, note the app versions. The Kubernetes components should be in `1.34.x` versions:

```bash
juju status

# output
Model          Controller      Cloud/Region         Version  SLA          Timestamp
canonical-k8s  lxd-controller  localhost/localhost  3.6.14   unsupported  12:26:26Z

App         Version  Status  Scale  Charm       Channel       Rev  Exposed  Message
k8s         1.34.3   active      1  k8s         1.34/stable  1844  no       Ready
k8s-worker  1.34.3   active      1  k8s-worker  1.34/stable  1841  no       Ready

Unit           Workload  Agent  Machine  Public address  Ports     Message
k8s-worker/0*  active    idle   1        10.237.75.27              Ready
k8s/0*         active    idle   0        10.237.75.10    6443/tcp  Ready

Machine  State    Address       Inst id        Base          AZ                           Message
0        started  10.237.75.10  juju-f36b6c-0  ubuntu@24.04  rpopescu.cloudbase.internal  Running
1        started  10.237.75.27  juju-f36b6c-1  ubuntu@24.04  rpopescu.cloudbase.internal  Running
```

We will upgrade to `1.35` stable version.

First, decide which updates are available:

```bash
juju status --format=json | \
   jq '.applications |
        to_entries[] | {
           application: .key,
           "charm-name": .value["charm-name"],
           "charm-channel": .value["charm-channel"],
           "charm-rev": .value["charm-rev"],
           "can-upgrade-to": .value["can-upgrade-to"]
        }'

# output
{
  "application": "k8s",
  "charm-name": "k8s",
  "charm-channel": "1.34/stable",
  "charm-rev": 1844,
  "can-upgrade-to": null
}
{
  "application": "k8s-worker",
  "charm-name": "k8s-worker",
  "charm-channel": "1.34/stable",
  "charm-rev": 1841,
  "can-upgrade-to": null
}
```

**NOTE**: if you see `"can-upgrade-to": null`, it means that there's no charm update available from the current channel.

Next, do a `pre-upgrade check` on the control plane:

```bash
juju run k8s/leader pre-upgrade-check

# output
Running operation 3 with 1 task
  - task 4 on unit-k8s-0

Waiting for task 4...
```

If there's no error, move the the upgrade process. Refresh the charm from another channel and watch the status:

```bash
juju refresh k8s --channel=1.35/stable
juju status k8s --watch 5s
```

The `refresh` command instructs the juju controller to follow a new charm channel. The Kubernetes charm will be upgraded to the latest revision within that channel. The charm code is simultaneously replaced on each unit, then the k8s snap is updated unit-by-unit in order to maintain a highly-available kube-api-server endpoint, starting with the Juju leader unit for each application.

After the upgrade shows it's completed, also verify node status:

```bash
kubectl get nodes

# output
NAME            STATUS   ROLES                  AGE   VERSION
juju-f36b6c-0   Ready    control-plane,worker   27h   v1.35.0
juju-f36b6c-1   Ready    worker                 27h   v1.34.3
```

The same `pre-upgrade-check` action needs to run on the worker units as well:

```bash
juju run k8s-worker/leader pre-upgrade-check
```

If the output is empty, it means the check passed, so we can safely proceed with the upgrade.

```bash
juju refresh k8s-worker --channel 1.35/stable
juju status k8s-worker --watch 5s
```

The `refresh` command instructs the juju controller to follow a new charm channel related to the Kubernetes release and use the new charm revision of the application’s channel to upgrade each unit. The charm code is simultaneously replaced on each unit, then the k8s snap is updated unit-by-unit, starting with the Juju leader unit for the application.

After the k8s-worker charm is upgraded, the application Version from juju status will reflect the updated version of the worker nodes making up the cluster.

Wait for it to settle, then check again your nodes:

```bash
kubectl get nodes

# output
NAME            STATUS   ROLES                  AGE   VERSION
juju-f36b6c-0   Ready    control-plane,worker   27h   v1.35.0
juju-f36b6c-1   Ready    worker                 27h   v1.35.0
```

After the `k8s-worker` charm is upgraded, the application Version from juju status will reflect the updated version of the worker nodes making up the cluster. Let's do a final `juju status` check:

```bash
juju status

# output
Model          Controller      Cloud/Region         Version  SLA          Timestamp
canonical-k8s  lxd-controller  localhost/localhost  3.6.14   unsupported  12:59:51Z

App         Version  Status  Scale  Charm       Channel       Rev  Exposed  Message
k8s         1.35.0   active      1  k8s         1.35/stable  1846  no       Ready
k8s-worker  1.35.0   active      1  k8s-worker  1.35/stable  1843  no       Ready

Unit           Workload  Agent  Machine  Public address  Ports     Message
k8s-worker/0*  active    idle   1        10.237.75.27              Ready
k8s/0*         active    idle   0        10.237.75.10    6443/tcp  Ready

Machine  State    Address       Inst id        Base          AZ                           Message
0        started  10.237.75.10  juju-f36b6c-0  ubuntu@24.04  rpopescu.cloudbase.internal  Running
1        started  10.237.75.27  juju-f36b6c-1  ubuntu@24.04  rpopescu.cloudbase.internal  Running
```



