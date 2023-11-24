import cv2
import numpy as np

class Affine():

    '''
        移動(m, my)のアフィン行列
       |x'|   | 1 0 mx| |x|
       |y'| = | 0 1 my| |y|
       | 1|   | 0 0 1 | |1|

       回転のアフィン行列(反時計回りにn度とすると)
       |x'|   | cos(n) -sin(n) 0 | |x|
       |y'| = | sin(n)  cos(n) 0 | |y|
       | 1|   |   0      0     1 | |1|
    '''

    CW0 = 0
    CW90 = 1
    CW180 = 2
    CW270 = 3
    UnKnown = 4

    @classmethod
    def make_matrix(cls, index, width, height):
        mat = []
        if index == 0:
            mat = [[1, 0, 0], [0, 1, 0]]
        elif index == 1:
            mat = Affine.make_CW90_cv2(width, height)
        elif index == 2:
            mat = Affine.make_CW180_cv2(width, height)
        elif index == 3:
            mat = Affine.make_CW270_cv2(width, height)
        else:
            raise IndexError('Out of Index')

        # 計算しやすいように3x3にする
        ret_mat = np.insert(mat, 2, [0, 0, 1], axis=0)
        return np.array(ret_mat, dtype=int)

    '''
    @classmethod
    def make_CW270_cv2(cls, width, height):
        src = np.float32([[0, 0], [width, 0], [width, height]])
        dest = np.float32([[height, 0], [height, width], [0, width]])
        mat = cv2.getAffineTransform(src, dest)
        return mat

    @classmethod
    def make_CW90_cv2(cls, width, height):
        src = np.float32([[0, 0], [width, 0], [width, height]])
        dest = np.float32([[0, width], [0, 0], [height, 0]])
        mat = cv2.getAffineTransform(src, dest)
        return mat

    @classmethod
    def make_CW180_cv2(cls, width, height):
        src = np.float32([[0, 0], [width, 0], [width, height]])
        dest = np.float32([[width, height], [0, height], [0, 0]])
        mat = cv2.getAffineTransform(src, dest)
        return mat
    '''
    @classmethod
    def make_CW270_cv2(cls, width, height):
        '''
        反時計回りに90度回転
        | 1 0 h/2|| cos(pi/2) -sin(pi/2) 0 || 1 0 -w/2|
        | 0 1 w/2|| sin(pi/2)  cos(pi/2) 0 || 0 1 -h/2|
        | 0 0  1 ||   0            0     1 || 0 0 1  |

          | 1 0 h/2|| 0 -1 0 || 1 0 -w/2| | 0 -1 h/2|| 1 0 -w/2| | 0 -1 h|
        = | 0 1 w/2|| 1  0 0 || 0 1 -h/2|=| 1  0 w/2|| 0 1 -h/2|=| 1 0  0|
          | 0 0  1 || 0  0 1 || 0 0  1  | | 0  0  1 || 0 0  1  | | 0 0  1|
        '''
        arr = [[0., -1., height], [1., 0., 0.]]
        return np.array(arr)

    @classmethod
    def make_CW180_cv2(cls, width, height):
        '''
        180度回転
        | 1 0 h/2|| cos(pi) -sin(pi) 0 || 1 0 -h/2|
        | 0 1 w/2|| sin(pi)  cos(pi) 0 || 0 1 -w/2|
        | 0 0  1 ||   0            0     1 || 0 0 1  |

          | 1 0 h/2|| -1 0 0 || 1 0 -h/2| | -1 0 h/2|| 1 0 -h/2| | -1 0 w|
        = | 0 1 w/2|| 0 -1 0 || 0 1 -w/2|=| 0 -1 w/2|| 0 1 -w/2|=| 0 -1 h|
          | 0 0  1 || 0  0 1 || 0 0  1  | | 0  0  1 || 0 0  1  | | 0 0  1|
        '''
        arr = [[-1., 0., width], [0., -1., height]]
        return np.array(arr)

    @classmethod
    def make_CW90_cv2(cls, width, height):
        '''
        時計回り90度回転
        | 1 0 h/2|| cos(pi/2*3) -sin(-pi/2*3) 0 || 1 0 -w/2|
        | 0 1 w/2|| sin(pi/2*3)  cos(-pi/2*3) 0 || 0 1 -h/2|
        | 0 0  1 ||   0            0     1 || 0 0 1  |

          | 1 0 h/2|| 0 1 0 || 1 0 -w/2| | -1 0 h/2 || 1 0 -h/2| | 0 1 0|
        = | 0 1 w/2||-1 0 0 || 0 1 -h/2|=| -1 0 w/2 || 0 1 -w/2|=|-1 0 w|
          | 0 0  1 || 0 0 1 || 0 0  1  | | 0  0  1  || 0 0  1  | | 0 0 1|
        '''
        arr = [[0., 1., 0.], [-1., 0., width]]
        return np.array(arr)

    @classmethod
    def translate(cls, matrix, rects):
        np_rects = np.array(rects, dtype=np.int)
        new_rect = np.dot(matrix, np_rects.T)
        return new_rect.T

