[Persian README (نسخه فارسی)](README.fa.md)

# Smart Home Vacuum Cleaning Simulator

This repository contains the base code for Firacup SmartHome built using Webots 2023.a. It is designed for a competition
where teams develop Python code to control a virtual vacuum cleaner and score points by efficiently cleaning the home
environment.

## Features

- Real-time vacuum cleaning simulation in a smart home environment.
- Teams compete by writing Python scripts to control the vacuum.
- Score is calculated based on the cleanliness of the home surface.

## Requirements

- [Webots R2023a](https://github.com/cyberbotics/webots/releases/download/R2023a/webots-R2023a_setup.exe)
- [Python 3.9.x Or 3.10.x](https://www.python.org/downloads/)

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/cnazk/Smart-Home.git
    ```

2. **Install Webots:**
   Download and install Webots 2023.a from the
   official [Webots website](https://github.com/cyberbotics/webots/releases/download/R2023a/webots-R2023a_setup.exe).

3. **Install Python packages:**
   Navigate to the project directory and install required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
   or
    ```bash
    pip install numpy pillow termcolor
    ```
   **You may also need to install any other packages you use**

4. **Additional Setup:**
   For detailed setup instructions, including setting up the simulation environment and Webots settings, refer to
   the [installation guide here](https://smarthomerobot.ir/?epkb_post_type_1=installation-guide-setting-up-your-simulation-environment).

## How to Run

1. Open the Webots simulator.

2. Load the project:
    - Go to `File -> Open World` and select the simulation world file from the `worlds/` directory.

   > [!NOTE]  
   > You can also double click on `U14.wbt` or `U19.wbt` files located in `game/worlds/` to open to map in webots.

3. Run the simulation:
    - The robot windows appears when the world loads (you can right-click on `MainSuperVisor` node from the list on the
      left and select `open robot window` to open it manually).
    - you can load your robot's code from that window and start the simulation.
   > [!IMPORTANT]  
   > Always make sure that the simulation is not paused from the webots toolbar.

4. There is a sample code in samples folder which is a good basecode to start working with SmartHome.

