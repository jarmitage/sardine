FROM python:3.10.7-bullseye

# Install dependencies
RUN apt update && apt install build-essential cmake -y

# Set working directory
WORKDIR /app

# Copy files from host to container
COPY ./ ./

# Install sardine requirements
RUN pip3 install -e .

# Install supercollider with noninteractive mode
RUN DEBIAN_FRONTEND='noninteractive' apt install supercollider -y

#  Enable sardine boot superdirt
RUN sardine-config --boot_superdirt=True

# Write in .bashrc file python -m fishery 
RUN echo "python -m fishery" >> ~/.bashrc

# Expose port for osc server
EXPOSE 23000

CMD ["/bin/bash"]

