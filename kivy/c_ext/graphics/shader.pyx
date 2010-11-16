__all__ = ('Shader', )

include "common.pxi"
from c_opengl cimport *

from numpy import ndarray, ascontiguousarray
from kivy.logger import Logger


cdef class Shader:
    '''Create a vertex or fragment shader

    :Parameters:
        `vert_src` : string
            source code for vertex shader
        `frag_src` : string
            source code for fragment shader
    '''
    def __cinit__(self):
        self.uniform_locations = dict()
        self.uniform_values = dict()


    def __init__(self, str vert_src, str frag_src):
        self.frag_src = frag_src
        self.vert_src = vert_src
        self.program = glCreateProgram()
        self.bind_attrib_locations()
        self.build()


    cdef use(self):
        '''Use the shader'''
        glUseProgram(self.program)
        for k,v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)


    cdef stop(self):
        '''Stop using the shader'''
        glUseProgram(0)


    cdef set_uniform(self, str name, value):
        self.uniform_values[name] = value
        self.upload_uniform(name, value)


    cdef upload_uniform(self, str name, value):
        '''Pass a uniform variable to the shader
        '''
        cdef int vec_size, loc
        val_type = type(value)
        loc = self.uniform_locations.get(name, self.get_uniform_loc(name))

        # TODO: use cython matrix transforms
        if val_type == ndarray:
            self.upload_uniform_matrix(name, value)
        elif val_type == int:
            glUniform1i(loc, value)
        elif val_type == float:
            glUniform1f(loc, value)
        else:
            #must have been a list, tuple, or other sequnce and be a vector uniform
            val_type = type(value[0])
            vec_size = len(value)
            if val_type == float:
                if vec_size == 2:
                    glUniform2f(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3f(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4f(loc, value[0], value[1], value[2], value[3])
            elif val_type == int:
                if vec_size == 2:
                    glUniform2i(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3i(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4i(loc, value[0], value[1], value[2], value[3])


    cdef upload_uniform_matrix(self, str name, value):
        #TODO: use cython matrix transforms
        cdef int loc = self.uniform_locations.get(name, self.get_uniform_loc(name))
        cdef GLfloat mat[16]
        np_flat = ascontiguousarray(value.T, dtype='float32').flatten()
        for i in range(16):
            mat[i] = <GLfloat>np_flat[i]
        glUniformMatrix4fv(loc, 1, False, mat)


    cdef int get_uniform_loc(self, str name):
        name_byte_str = name
        cdef char* c_name = name_byte_str
        cdef int loc = glGetUniformLocation(self.program, c_name)
        self.uniform_locations[name] = loc
        return loc


    cdef bind_attrib_locations(self):
        cdef char* c_name
        for attr in VERTEX_ATTRIBUTES:
            c_name = attr['name']
            glBindAttribLocation(self.program, attr['index'], c_name)
            if attr['per_vertex']:
                glEnableVertexAttribArray(attr['index'])


    cdef build(self):
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        glAttachShader(self.program, self.vertex_shader)
        glAttachShader(self.program, self.fragment_shader)
        glLinkProgram(self.program)
        self.uniform_locations = dict()
        self.process_build_log()


    cdef compile_shader(self, char* source, shadertype):
        shader = glCreateShader(shadertype)
        glShaderSource(shader, 1, <GLchar**> &source, NULL)
        glCompileShader(shader)
        return shader


    cdef get_shader_log(self, shader):
        '''Return the shader log'''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetShaderInfoLog(shader, 2048, NULL, msg)
        return msg


    cdef get_program_log(self, shader):
        '''Return the program log'''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetProgramInfoLog(shader, 2048, NULL, msg)
        return msg


    cdef process_build_log(self):
        self.process_message('vertex shader', self.get_shader_log(self.vertex_shader))
        self.process_message('fragment shader', self.get_shader_log(self.fragment_shader))
        self.process_message('program', self.get_program_log(self.program))
        error = glGetError()
        if error:
            Logger.error('GShader: GL error %d' % error)


    cdef process_message(self, str ctype, str message):
        if message:
            Logger.error('GShader: %s: %s' % (ctype, message))
            raise Exception(message)
        else:
            Logger.debug('GShader: %s compiled successfully' % ctype)




