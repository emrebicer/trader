
# Build container
docker build -t ssb .

# Run container
docker run -it -d -v "$(pwd):/app/" ssb