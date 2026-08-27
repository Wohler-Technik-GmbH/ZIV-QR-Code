# PowerShell script for building the Podman image and starting the container

$imageName = "qr-code-scanner-image"
$containerName = "qr-code-scanner"
$hostPort = 8080
$containerPort = 8080
$containerFile = "Containerfile"

# Step 1: Build the Podman image
Write-Host "Building Podman image '$imageName'..." -ForegroundColor Blue
podman build -t $imageName -f $containerFile .
#podman build --no-cache -t $imageName -f $containerFile .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error building Podman image." -ForegroundColor Red
    exit 1
}
Write-Host "Podman image '$imageName' successfully built." -ForegroundColor Green

# Step 2: Start the container
Write-Host "Starting Podman container '$containerName' from image '$imageName'..." -ForegroundColor Blue
podman run --rm -p ${hostPort}:${containerPort} --name $containerName $imageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error starting Podman container." -ForegroundColor Red
    # Attempt to stop and remove any existing container with the same name if the start failed
    Write-Host "Attempting to stop and remove any existing container '$containerName'..."
    podman stop $containerName | Out-Null
    podman rm $containerName | Out-Null
    exit 1
}