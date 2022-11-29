import glm
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr


class Cube:
    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

class Obj:
    def __init__(self, filename):
        
        self.vertices = self.loadObj(filename)
        self.vertex_count = len(self.vertices)//8
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

    def loadObj(self, filename):
        v = []
        vt = []
        vn = []
        
        vertices = []

        # Obj decomposition
        with open(filename,'r') as f:
            
            line = f.readline()
            
            while line:
                firstSpace = line.find(" ")
                flag = line[0:firstSpace]
                
                if flag=="v":
                    
                    line = line.replace("v ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    v.append(l)
                
                elif flag=="vt":
                    
                    line = line.replace("vt ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vt.append(l)
                elif flag=="vn":
                    #normal
                    line = line.replace("vn ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vn.append(l)
                elif flag=="f":
                    #caras
                    line = line.replace("f ","")
                    line = line.replace("\n","")
                    line = line.split(" ")
                    self.faceVertices = []
                    faceTextures = []
                    faceNormals = []
                    for vertex in line:
                        l = vertex.split("/")
                        position = int(l[0]) - 1
                        self.faceVertices.append(v[position])
                        texture = int(l[1]) - 1
                        faceTextures.append(vt[texture])
                        normal = int(l[2]) - 1
                        faceNormals.append(vn[normal])
                    triangles_in_face = len(line) - 2

                    vertex_order = []
                  
                    for i in range(triangles_in_face):
                        vertex_order.append(0)
                        vertex_order.append(i+1)
                        vertex_order.append(i+2)
                    for i in vertex_order:
                        for x in self.faceVertices[i]:
                            vertices.append(x)
                        for x in faceTextures[i]:
                            vertices.append(x)
                        for x in faceNormals[i]:
                            vertices.append(x)
                line = f.readline()
        
        return vertices

class Renderer:
    def __init__(self, obj, position):
        
        #initialize pygame
        pygame.init()

        # Display configuration
        pygame.display.set_mode((800, 800), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption('MODEL VIEWER')
        
        #initialize opengl
        glClearColor(0.8, 0.8, 0.8, 1)
        self.cube_mesh = Obj(obj)

        vertex_shader = """
        #version 460
        layout (location=0) in vec3 vertexPos;
        layout (location=1) in vec2 vertexTexCoord;

        uniform mat4 model;
        uniform mat4 projection;

        out vec3 posicion;

        void main()
        {
            gl_Position = projection * model * vec4(vertexPos, 1.0);
            posicion = vertexPos;
        }
        """
        
        fragment_shader = """
        #version 460
        in vec3 posicion;

        uniform vec3 type;
        uniform vec3 fragmentColor1;
        uniform vec3 fragmentColor2;
        uniform vec3 fragmentColor3;

        out vec4 color;

        void shader1(){
            if (posicion.x >= 0.35){
                color = vec4(fragmentColor1, 1.0f);
            } else if (posicion.x < 0.35 && posicion.x >= -0.35) {
                color = vec4(fragmentColor2, 1.0f);
            } else {
                color = vec4(fragmentColor3, 1.0f);
            }
        }

        void shader2(){
            if (posicion.y >= 0.15){
                color = vec4(fragmentColor2, 1.0f);
            } else if (posicion.y< 0.15 && posicion.y >= -0.45) {
                color = vec4(fragmentColor1, 1.0f);
            } else {
                color = vec4(fragmentColor3, 1.0f);
            }
        }
        
        void shader3(){
            if (posicion.y >= 0.60){
                color = vec4(fragmentColor2, 4.0f);
            } else if (posicion.y< 0.15 && posicion.y >= -0.25) {
                color = vec4(fragmentColor1, 1.0f);
            } else {
                color = vec4(fragmentColor3, 1.0f);
            }
        }

        void main()
        {
            if (type.x == 1){
                shader1();
            } else if (type.x == 2) {
                shader2();
            } if (type.x == 3) {
                shader3();
            }
        }
        """

        self.compiled_vertex_shader = compileShader(vertex_shader, GL_VERTEX_SHADER)
        self.compiled_fragment_shader = compileShader(fragment_shader, GL_FRAGMENT_SHADER)

        self.shader = compileProgram(
            self.compiled_vertex_shader,
            self.compiled_fragment_shader
        )
        glUseProgram(self.shader)
        glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)
        glEnable(GL_DEPTH_TEST)

        self.cube = Cube(
            position = position,
            eulers = [0, 0, 0]
        )

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640 / 480, 
            near = 0.1, far = 10, dtype=np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"),
            1, GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")

    def render_obj(self,num):
        running = True

        while (running):
            
            # Shader options
            if num == 1:
                self.shader1()
            elif num == 2:
                self.shader2()
            elif num == 3:
                self.shader3()
            
            for event in pygame.event.get():
                if (event.type == pygame.QUIT):
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        self.cube.eulers[2] += 5
                    if event.key == pygame.K_LEFT:
                        self.cube.eulers[2] -= 5
                    if event.key == pygame.K_UP:
                        self.cube.eulers[0] += 5
                    if event.key == pygame.K_DOWN:
                        self.cube.eulers[0] -= 5
                    if event.key == pygame.K_a:
                        self.cube.eulers[1] -= 5
                    if event.key == pygame.K_d:
                        self.cube.eulers[1] += 5
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.shader)

            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
           
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_eulers(
                    eulers=np.radians(self.cube.eulers), dtype=np.float32
                )
            )
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_translation(
                    vec=np.array(self.cube.position),dtype=np.float32
                )
            )
            
            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
            
            glDrawArrays(GL_TRIANGLES, 0, self.cube_mesh.vertex_count)

            pygame.display.flip()

            pygame.time.wait(100)

    def shader1(self):
        black = glm.vec3(0, 0, 0)   
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor1'),
            1,
            glm.value_ptr(black)
        )

        white = glm.vec3(255, 255, 255)
        glUniform3fv(
            glGetUniformLocation(self.shader, 'fragmentColor2'),
            1,
            glm.value_ptr(white)
        )
        
        glUniform3fv(
            glGetUniformLocation(self.shader, 'fragmentColor3'),
            1,
            glm.value_ptr(black)
        )

        type = glm.vec3(1, 0, 0)
        glUniform3fv(
            glGetUniformLocation(self.shader, 'type'),
            1,
            glm.value_ptr(type)
        )

    def shader2(self):
        red = glm.vec3(255, 0, 0)   
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor1'),
            1,
            glm.value_ptr(red)
        )

        white = glm.vec3(255, 255, 255)
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor2'),
            1,
            glm.value_ptr(white)
        )
        
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor3'),
            1,
            glm.value_ptr(red)
        )

        type = glm.vec3(1, 0, 0)
        glUniform3fv(
            glGetUniformLocation(self.shader,'type'),
            1,
            glm.value_ptr(type)
        )
    
    def shader3(self):
        blue = glm.vec3(0, 0, 255)   
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor1'),
            1,
            glm.value_ptr(blue)
        )

        white = glm.vec3(255, 255, 255)
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor2'),
            1,
            glm.value_ptr(white)
        )
        
        green = glm.vec3(0, 255, 0)
        glUniform3fv(
            glGetUniformLocation(self.shader,'fragmentColor3'),
            1,
            glm.value_ptr(green)
        )

        type = glm.vec3(1, 0, 0)
        glUniform3fv(
            glGetUniformLocation(self.shader,'type'),
            1,
            glm.value_ptr(type)
        )


'''
 ================================================================
 PROGRAM EXECUTION
 ================================================================
'''

model = 'cube.obj'

position = [0, 0, -5]

r = Renderer(model, position)

r.render_obj(3)