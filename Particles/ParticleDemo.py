from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, VBase4, loadPrcFileData, NodePath, PointLight, LVector3, TransparencyAttrib
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpFunc, Func, Wait

# Configuration to disable the default splash window for cleaner execution
loadPrcFileData("", "notify-level-audio error")
loadPrcFileData("", "window-title Panda3D Simple Particle Demo (Intervals)")
loadPrcFileData("", "show-frame-rate-meter true")

class ParticleDemo(ShowBase):
    """
    A simple Panda3D application demonstrating a fire/spark effect using 
    Panda3D's robust Task and Interval system instead of the legacy 
    direct.particles module, bypassing common import errors.
    """
    def __init__(self):
        ShowBase.__init__(self)

        # --- 1. Basic Scene Setup ---
        self.setBackgroundColor(0.0, 0.0, 0.1, 1) # Dark background
        self.cam.setPos(0, -30, 10)
        self.cam.lookAt(0, 0, 0)
        
        # List to hold active particle NodePaths
        self.active_particles = []
        self.max_particles = 100

        # Set up a light source to illuminate the particles
        plight = PointLight('plight')
        plight.setColor(VBase4(1, 0.5, 0.2, 1)) # Orange light
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(0, 0, 5)
        self.render.setLight(plnp)
        
        # Load a simple cube to show the particle source location
        try:
            box = self.loader.loadModel("models/misc/cube")
            box.reparentTo(self.render)
            box.setScale(0.5)
            box.setColor(0.5, 0.1, 0.1, 1)
            box.setZ(0) # Center the box
        except Exception as e:
            print(f"Cube model not found: {e}. Proceeding without it.")


        # --- 2. Particle Task Setup ---
        # Add a task to continuously spawn new particles
        self.taskMgr.doMethodLater(0.01, self.spawn_particle, "SpawnParticleTask")

    def spawn_particle(self, task):
        """Spawns a new particle and starts its life cycle animation."""
        
        # Control particle count
        if len(self.active_particles) >= self.max_particles:
            return Task.cont

        # 1. Create the particle (a simple sphere/point for visual effect)
        particle = self.loader.loadModel("models/misc/sphere")
        particle.reparentTo(self.render)
        
        # Initial properties
        initial_scale = 0.1 + (0.2 * (0.5 - globalClock.getFrameTime()) % 1)
        particle.setScale(initial_scale)
        particle.setPos(0, 0, 0.5) # Start slightly above the cube
        
        # Random initial velocity/direction for a fiery spread
        rand_x = (0.5 - (globalClock.getFrameTime() * 1.1) % 1) * 2 # -1.0 to 1.0
        rand_y = (0.5 - (globalClock.getFrameTime() * 1.3) % 1) * 2 # -1.0 to 1.0
        
        # Define life properties
        life_duration = 1.0 + (globalClock.getFrameTime() * 0.5) % 1 # 1.0 to 2.0 seconds
        final_z = 5.0 + life_duration * 1.5 # How high it rises

        # 2. Define the Particle Animation (Intervals)
        
        # A. Movement: Move upwards with some horizontal drift
        move_interval = particle.posInterval(
            life_duration,
            pos=LVector3(rand_x * 0.5, rand_y * 0.5, final_z),
            startPos=particle.getPos()
        )
        
        # B. Scaling and Fading (Visuals)
        # Scale: Grows slightly then shrinks to 0.0
        scale_up = particle.scaleInterval(life_duration * 0.2, initial_scale * 1.5, startScale=initial_scale)
        scale_down = particle.scaleInterval(life_duration * 0.8, 0.0, startScale=initial_scale * 1.5)
        scale_sequence = Sequence(scale_up, scale_down)
        
        # Color: Lerp (interpolate) from bright yellow/orange to dark transparent
        color_start = VBase4(1.0, 0.8, 0.2, 1.0) # Yellow/Orange
        color_end = VBase4(0.1, 0.1, 0.1, 0.0) # Dark/Transparent (Smoke)
        
        color_interval = LerpFunc(
            self.update_color_and_alpha,
            duration=life_duration,
            fromData=0.0,
            toData=1.0,
            extraArgs=[particle, color_start, color_end]
        )

        # 3. Combine animations and deletion (Life Cycle)
        # Parallel runs movement, scale, and color at the same time
        # Sequence ensures it's removed after all animations complete
        life_cycle = Sequence(
            Parallel(move_interval, scale_sequence, color_interval),
            Func(self.destroy_particle, particle) # Function to clean up the particle
        )
        
        life_cycle.start()
        self.active_particles.append(particle)
        
        return Task.cont

    def update_color_and_alpha(self, t, particle, start_color, end_color):
        """Custom LerpFunc to handle color and alpha interpolation."""
        
        # Simple linear interpolation
        r = start_color[0] * (1-t) + end_color[0] * t
        g = start_color[1] * (1-t) + end_color[1] * t
        b = start_color[2] * (1-t) + end_color[2] * t
        a = start_color[3] * (1-t) + end_color[3] * t

        particle.setColor(VBase4(r, g, b, a), 1) # Set the color with a priority (1)
        
        # Enable transparency
        particle.setTransparency(TransparencyAttrib.MAlpha)

    def destroy_particle(self, particle):
        """Removes the particle from the scene and the active list."""
        if particle in self.active_particles:
            self.active_particles.remove(particle)
        particle.removeNode()

# Run the application
if __name__ == "__main__":
    app = ParticleDemo()
    app.run()