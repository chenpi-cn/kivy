'''
Scatter
=======

'''

__all__ = ('Scatter', )

from math import radians
from numpy import ascontiguousarray
from kivy.properties import BooleanProperty, AliasProperty, \
        NumericProperty, NumpyProperty
from kivy.vector import Vector
from kivy.uix.widget import Widget
from kivy.lib.transformations import matrix_multiply, identity_matrix, \
        translation_matrix, rotation_matrix, scale_matrix, inverse_matrix

class Scatter(Widget):

    #: Allow translation on X axis
    do_translation_x = BooleanProperty(True)

    #: Allow translation on Y axis
    do_translation_y = BooleanProperty(True)

    def _get_do_translation(self):
        return (self.do_translation_x, self.do_translation_y)
    def _set_do_translation(self, value):
        if type(value) in (list, tuple):
            self.do_translation_x, self.do_translation_y = value
        else:
            self.do_translation_x = self.do_translation_y = bool(value)
    #: Allow translation on X or Y axis
    do_translation = AliasProperty(_get_do_translation, _set_do_translation,
                                   bind=('do_translation_x', 'do_translation_y'))


    #: Allow rotation
    do_rotation = BooleanProperty(True)

    #: Allow scaling
    do_scale = BooleanProperty(True)

    #: Minimum scaling allowed
    scale_min = NumericProperty(0.01)

    #: Maximum scaling allowed
    scale_max = NumericProperty(1e20)

    #: Transformation matrice
    transform = NumpyProperty(identity_matrix())

    #: Inverse of the transformation matrice
    transform_inv = NumpyProperty(identity_matrix())

    def __init__(self, **kwargs):
        self._touches = []
        self._last_touch_pos = {}
        self._transform_gl     = ascontiguousarray(identity_matrix().T,
                                                   dtype='float32')

        super(Scatter, self).__init__(**kwargs)

        '''
        # inital transformation
        self.scale = kwargs.get('scale', 1)
        self.rotation = kwargs.get('rotation', 0)
        if kwargs.get('pos') and kwargs.get('center'):
            pymt_logger.exception('both "pos" and "center" set in MTScatter'
                                  'constructor, only use one of the two!')
        if kwargs.get('pos'):
            self.pos = kwargs.get('pos')
        if kwargs.get('center'):
            self.pos = kwargs.get('center')
        '''

    def _get_bbox(self):
        '''
        Returns the bounding box of the widget in parent space ::

            ((x, y), (w, h)
            # x, y = lower left corner

        '''
        xmin, ymin = xmax, ymax = self.to_parent(0, 0)
        for point in [(self.width, 0), (0, self.height), self.size]:
            x, y = self.to_parent(*point)
            if x < xmin:
                xmin = x
            if y < ymin:
                ymin = y
            if x > xmax:
                xmax = x
            if y > ymax:
                ymax = y
        return (xmin, ymin), (xmax-xmin, ymax-ymin)
    bbox = AliasProperty(_get_bbox, None, bind=(
        'transform', 'width', 'height'))

    def _get_center(self):
        return (self.bbox[0][0] + self.bbox[1][0]/2.0,
                self.bbox[0][1] + self.bbox[1][1]/2.0)
    def _set_center(self, center):
        if center == self.center:
            return False
        t = Vector(*center) - self.center
        trans = translation_matrix( (t.x, t.y, 0) )
        self.apply_transform(trans)
    center = AliasProperty(_get_center, _set_center, bind=('bbox', ))

    def _get_pos(self):
        return self.bbox[0]
    def _set_pos(self, pos):
        _pos = self.bbox[0]
        if pos == _pos:
            return
        t = Vector(*pos) - _pos
        trans = translation_matrix( (t.x, t.y, 0) )
        self.apply_transform(trans)
    pos = AliasProperty(_get_pos, _set_pos, bind=('bbox', ))

    def _get_x(self):
        return self.bbox[0][0]
    def _set_x(self, x):
        if x == self.bbox[0][0]:
            return False
        self.pos = (x, self.y)
        return True
    x = AliasProperty(_get_x, _set_x, bind=('bbox', ))

    def _get_y(self):
        return self.bbox[0][1]
    def _set_y(self, y):
        if y == self.bbox[0][1]:
            return False
        self.pos = (self.x, y)
        return True
    y = AliasProperty(_get_y, _set_y, bind=('bbox', ))

    def _get_rotation(self):
        v1 = Vector(0, 10)
        v2 = Vector(*self.to_parent(*self.pos)) - self.to_parent(self.x, self.y + 10)
        return -1.0 *(v1.angle(v2) + 180) % 360
    def _set_rotation(self, rotation):
        angle_change = self.rotation - rotation
        r = rotation_matrix(-radians(angle_change), (0, 0, 1))
        self.apply_transform(r, post_multiply=True, anchor=self.to_local(*self.center))
    #: Rotation value in degrees
    rotation = AliasProperty(_get_rotation, _set_rotation, bind=(
        'x', 'y', 'transform'))

    def _get_scale(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)
        return float(scale)
    def _set_scale(self, scale):
        #scale = boundary(scale, self.scale_min, self.scale_max) 
        rescale = scale * 1.0 / self.scale
        self.apply_transform(scale_matrix(rescale), post_multiply=True, anchor=self.to_local(*self.center))
    #: Scale value
    scale = AliasProperty(_get_scale, _set_scale, bind=('x', 'y', 'transform'))

    @property
    def transform_gl(self):
        '''Return the transformation matrix for OpenGL, read only.
        '''
        return self._transform_gl

    def on_transform(self, instance, value):
        self.transform_inv = inverse_matrix(value)
        self._transform_gl = ascontiguousarray(self.transform.T,
                                               dtype='float32')

    """
    def _get_state(self):
        return serialize_numpy(self.transform)
    def _set_state(self, state):
        self.transform = deserialize_numpy(state)
    state = property(_get_state, _set_state,
        doc='Save/restore the state of matrix widget (require numpy)')
    """

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return 0 <= x <= self.width and 0 <= y <= self.height

    def to_parent(self, x, y, **k):
        p = matrix_multiply(self.transform, (x, y, 0, 1))
        return (p[0], p[1])

    def to_local(self, x, y, **k):
        p = matrix_multiply(self.transform_inv, (x, y, 0, 1))
        return (p[0], p[1])

    def apply_angle_scale_trans(self, angle, scale, trans, point=Vector(0, 0)):
        '''Update matrix transformation by adding new angle, scale and translate.

        :Parameters:
            `angle` : float
                Rotation angle to add
            `scale` : float
                Scaling value to add
            `trans` : Vector
                Vector translation to add
            `point` : Vector, default to (0, 0)
                Point to apply transformation
        '''
        old_scale = self.scale
        new_scale = old_scale * scale
        if new_scale < self.scale_min or old_scale > self.scale_max:
            scale = 1.

        t = translation_matrix((
            trans[0] * self.do_translation_x,
            trans[1] * self.do_translation_y,
            0
        ))
        t = matrix_multiply(t, translation_matrix( (point[0], point[1], 0)))
        t = matrix_multiply(t, rotation_matrix(angle, (0, 0, 1)))
        t = matrix_multiply(t, scale_matrix(scale))
        t = matrix_multiply(t, translation_matrix((-point[0], -point[1], 0)))
        self.apply_transform(t)

    def apply_transform(self, trans, post_multiply=False, anchor=(0, 0)):
        '''
        Transforms scatter by trans (on top of its current transformation state)

        :Parameters:
            `trans`: transformation matrix from transformation lib.
                Transformation to be applied to the scatter widget
            `anchor`: tuple, default to (0, 0)
                The point to use as the origin of the transformation
                (uses local widget space)
            `post_multiply`: bool, default to False
                If true the transform matrix is post multiplied
                (as if applied before the current transform)
        '''
        t = translation_matrix( (anchor[0], anchor[1], 0) )
        t = matrix_multiply(t, trans)
        t = matrix_multiply(t, translation_matrix( (-anchor[0], -anchor[1], 0) ))

        if post_multiply:
            self.transform = matrix_multiply(self.transform, t)
        else:
            self.transform = matrix_multiply(t, self.transform)

    def _apply_drag(self, touch):
        # _last_touch_pos has last pos in correct parent space, just liek incoming touch
        dx = (touch.x - self._last_touch_pos[touch][0]) * self.do_translation_x
        dy = (touch.y - self._last_touch_pos[touch][1]) * self.do_translation_y
        self.apply_transform(translation_matrix((dx, dy, 0)))

    def transform_with_touch(self, touch):
        # just do a simple one finger drag
        if len(self._touches) == 1:
            return self._apply_drag(touch)

        # we have more than one touch...
        points = [Vector(*self._last_touch_pos[t]) for t in self._touches]

        # we only want to transform if the touch is part of the two touches
        # furthest apart! So first we find anchor, the point to transform
        # around as the touch farthest away from touch
        anchor  = max(points, key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if points.index(farthest) != self._touches.index(touch):
            return

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation        
        old_line = Vector(*touch.dpos) - anchor
        new_line = Vector(*touch.pos) - anchor

        angle = radians( new_line.angle(old_line) ) * self.do_rotation
        scale = new_line.length() / old_line.length()
        new_scale = scale * self.scale
        if new_scale < self.scale_min or new_scale > self.scale_max:
            scale = 1.0

        self.apply_transform(rotation_matrix(angle, (0, 0, 1)), anchor=anchor)
        self.apply_transform(scale_matrix(scale), anchor=anchor)

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y

        # if the touch isnt on the widget we do nothing
        if not self.collide_point(x, y):
            return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            touch.pop()
            return True
        touch.pop()

        # grab the touch so we get all it later move events for sure
        touch.grab(self)
        self._last_touch_pos[touch] = touch.pos
        self._touches.append(touch)

        return True

    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        # let the child widgets handle the event if they want
        if self.collide_point(x, y) and not touch.grab_current == self:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_move(touch):
                touch.pop()
                return True
            touch.pop()

        # rotate/scale/translate
        if touch in self._touches and touch.grab_current == self:
            self.transform_with_touch (touch)
            self._last_touch_pos[touch] = touch.pos

        # stop porpagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_touch_up(self, touch):
        x, y = touch.x, touch.y
        # if the touch isnt on the widget we do nothing, just try children
        if not touch.grab_current == self:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_up(touch):
                touch.pop()
                return True
            touch.pop()

        # remove it from our saved touches
        if touch in self._touches and touch.grab_state:
            touch.ungrab(self)
            del self._last_touch_pos[touch]
            self._touches.remove(touch)

        # stop porpagating if its within our bounds
        if self.collide_point(x, y):
            return True
