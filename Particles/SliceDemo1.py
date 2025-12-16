from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, VBase4, loadPrcFileData, NodePath, PointLight, LVector3, 
    TransparencyAttrib, DirectionalLight, 
    CardMaker, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, GeomNode
)
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpFunc, Func, Wait

# Konfiguráció az ablak beállításaihoz
loadPrcFileData("", "notify-level-audio error")
loadPrcFileData("", "window-title Panda3D Kivágás (Slice) Effekt") # Window title in Hungarian
loadPrcFileData("", "show-frame-rate-meter true")

# Kocka geometria generálása a fájlbetöltési hibák elkerülése érdekében
def create_cube_mesh():
    """Generates a cube mesh programmatically."""
    format = GeomVertexFormat.getV3n3t2()
    vdata = GeomVertexData('cube_data', format, Geom.UHStatic)
    
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    texcoord = GeomVertexWriter(vdata, 'texcoord')

    # Fél méret (a középpontból)
    s = 0.5 

    # Kocka csúcsai (8 csúcs)
    points = [
        (-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (-s,  s, -s),  # Alsó lap
        (-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (-s,  s,  s)   # Felső lap
    ]

    # Felületek (6 felület, 4 csúcs/felület, 2 háromszög/felület = 36 index)
    faces = [
        # Elülső
        0, 1, 2, 3, 
        # Hátsó
        4, 7, 6, 5, 
        # Jobb
        1, 5, 6, 2, 
        # Bal
        0, 3, 7, 4, 
        # Felső
        3, 2, 6, 7, 
        # Alsó
        0, 4, 5, 1
    ]

    # Normálok
    normals = [
        ( 0, -1,  0), # Elülső
        ( 0,  1,  0), # Hátsó
        ( 1,  0,  0), # Jobb
        (-1,  0,  0), # Bal
        ( 0,  0,  1), # Felső
        ( 0,  0, -1)  # Alsó
    ]

    # A kocka létrehozása a felületek és háromszögek hozzáadásával
    prim = GeomTriangles(Geom.UHStatic)
    for i in range(6): # 6 felület
        # 4 csúcsot használunk minden felülethez (a textúra koordináták miatt ismételjük a pontokat)
        
        # Első háromszög
        p1 = points[faces[i*4 + 0]]
        p2 = points[faces[i*4 + 1]]
        p3 = points[faces[i*4 + 2]]
        
        # Második háromszög
        p4 = points[faces[i*4 + 0]]
        p5 = points[faces[i*4 + 2]]
        p6 = points[faces[i*4 + 3]]
        
        tris = [p1, p2, p3, p4, p5, p6]
        
        for k in range(6):
            vertex.addData3f(tris[k][0], tris[k][1], tris[k][2])
            normal.addData3f(normals[i][0], normals[i][1], normals[i][2])
            
            # Textúra koordináták, egyszerűen a felület sarkait használva
            if k == 0 or k == 3: texcoord.addData2f(0.0, 0.0)
            elif k == 1: texcoord.addData2f(1.0, 0.0)
            elif k == 2 or k == 4: texcoord.addData2f(1.0, 1.0)
            elif k == 5: texcoord.addData2f(0.0, 1.0)

        # Minden felülethez két háromszöget adunk hozzá (összesen 12)
        v_offset = i * 6
        prim.addVertices(v_offset + 0, v_offset + 1, v_offset + 2)
        prim.addVertices(v_offset + 3, v_offset + 4, v_offset + 5)
        
    geom = Geom(vdata)
    geom.addPrimitive(prim)
    
    node = GeomNode('cube_geom')
    node.addGeom(geom)
    
    return NodePath(node)

class ParticleDemo(ShowBase):
    """
    Panda3D alkalmazás, amely a legacy részecskemodulok helyett 
    Interval és Task rendszert használ egy íves, elhalványuló vágáscsík (slice) 
    effektus szimulálására. Minden vizuális elem (kocka) mesh-ből generálódik.
    """
    def __init__(self):
        ShowBase.__init__(self)

        # --- 1. Alapvető helyszín beállítása ---
        # Sötét háttér a fehér csík kiemeléséhez
        self.setBackgroundColor(0.05, 0.05, 0.1, 1) 
        self.cam.setPos(0, -30, 5)
        self.cam.lookAt(0, 0, 3)
        
        # Aktív részecskéket tároló lista
        self.active_particles = []
        self.max_particles = 80 # Kevésbé sűrű, 'swoosh' hatás
        
        # A fényforrás beállítása
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(0.8, 0.8, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        # Ambient fény a láthatóságért
        alight = AmbientLight('alight')
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # --- GENERÁTOR KOCKA BEÁLLÍTÁSA ---
        # Generáljuk a kockát mesh-ből a fájlbetöltési hibák elkerülése végett
        generator_cube = create_cube_mesh()
        generator_cube.reparentTo(self.render)
        generator_cube.setScale(2.0, 2.0, 2.0) # Nagyobb méret
        generator_cube.setPos(0, 0, 2.0) # Középre, a csíkok kiindulási pontjához közel
        
        # Átlátszó, sötét színű vizuális generátor
        generator_cube.setColor(0.1, 0.1, 0.3, 0.5) # Sötétkék, 50% átlátszóság
        generator_cube.setTransparency(TransparencyAttrib.MAlpha)
        # --- GENERÁTOR KOCKA VÉGE ---

        # --- 2. Részecske (Csík) Kezelő Feladat Beállítása ---
        # Folyamatosan indít új csíkot a láthatósági időtartamon belül
        self.taskMgr.doMethodLater(0.1, self.spawn_particle, "SpawnSliceTask")

    def spawn_particle(self, task):
        """Létrehoz egy új csík-részecskét és elindítja az életciklus-animációját."""
        
        # Részecskeszám ellenőrzése
        if len(self.active_particles) >= self.max_particles:
            return Task.cont

        # 1. Részecske létrehozása (kocka modell, amit csíkká nyújtunk)
        # Generáljuk a részecske mesh-ét is
        particle = create_cube_mesh()
        particle.reparentTo(self.render)
        
        # --- Kezdeti Tulajdonságok a Csík Effektushoz ---
        life_duration = 1.0 # Az animáció teljes időtartama
        
        # Skálázás: Vékony és hosszú a csík (X: vastagság, Y: hossz)
        initial_scale_x = 0.03
        initial_scale_y = 5.0  
        particle.setScale(initial_scale_x, initial_scale_y, 0.03)
        
        # Kezdő és végpontok beállítása 
        # A csík a balról jobbra (X) és enyhén felfelé (Z) halad
        # A csíkok a generátor kocka Z pozíciójából indulnak (~2.0)
        start_x = -15
        start_y = (0.5 - (globalClock.getFrameTime() * 1.7) % 1) * 5 # Véletlenszerű Y pozíció 
        start_z = 2.0 + (0.5 - (globalClock.getFrameTime() * 1.5) % 1) * 2 # A generátor kocka Z magasságából indul
        start_pos = LVector3(start_x, start_y, start_z)
        particle.setPos(start_pos) 
        
        # --- 2. Részecske Animáció (Intervalok) ---
        
        # A. Mozgás: Ívelt pálya két szakaszban (Bezier-szerű mozgás szimulálása)
        end_pos = LVector3(15, start_y - 2, start_z + 4) 
        
        # Kontrollpont a hajlított mozgáshoz (először fel, majd le)
        mid_pos = LVector3(0, start_y + 3, start_z + 5) 
        
        # 1. szakasz: Felhúzás a kontrollpontig
        move1 = particle.posInterval(
            life_duration * 0.4,
            pos=mid_pos,
            startPos=start_pos
        )
        
        # 2. szakasz: Ívben tovább a végpontig
        move2 = particle.posInterval(
            life_duration * 0.6,
            pos=end_pos,
            startPos=mid_pos
        )
        move_sequence = Sequence(move1, move2) # Ívelt pálya
        
        # B. Skálázás és Elforgatás
        # A csík hosszának gyors zsugorítása az időtartam alatt
        scale_down = particle.scaleInterval(life_duration, LVector3(0.01, 0.01, 0.01), startScale=particle.getScale())
        
        # Enyhe elforgatás
        rotation = particle.hprInterval(life_duration, LVector3(20, 0, 0))

        # C. Szín: Fehérről átlátszóra halványodás
        color_start = VBase4(1.0, 1.0, 1.0, 1.0) # Fehér, teljesen átlátszatlan
        color_end = VBase4(0.8, 0.8, 0.9, 0.0) # Világos, teljesen átlátszó

        color_interval = LerpFunc(
            self.update_color_and_alpha,
            duration=life_duration,
            fromData=0.0,
            toData=1.0,
            extraArgs=[particle, color_start, color_end]
        )

        # 3. Animációk és takarítás kombinálása (Életciklus)
        life_cycle = Sequence(
            # A mozgás, skálázás, forgatás és színváltás párhuzamosan fut
            Parallel(move_sequence, scale_down, rotation, color_interval),
            Func(self.destroy_particle, particle) # Törlés az animáció végén
        )
        
        life_cycle.start()
        self.active_particles.append(particle)
        
        return Task.cont

    def update_color_and_alpha(self, t, particle, start_color, end_color):
        """Egyéni LerpFunc a szín- és alfa-interpoláció kezelésére."""
        
        # Lineáris interpoláció
        r = start_color[0] * (1-t) + end_color[0] * t
        g = start_color[1] * (1-t) + end_color[1] * t
        b = start_color[2] * (1-t) + end_color[2] * t
        a = start_color[3] * (1-t) + end_color[3] * t

        particle.setColor(VBase4(r, g, b, a), 1) 
        
        # Átlátszóság engedélyezése
        particle.setTransparency(TransparencyAttrib.MAlpha)

    def destroy_particle(self, particle):
        """Eltávolítja a részecskét a jelenetből és az aktív listából."""
        if particle in self.active_particles:
            self.active_particles.remove(particle)
        particle.removeNode()

# Az alkalmazás futtatása
if __name__ == "__main__":
    app = ParticleDemo()
    app.run()