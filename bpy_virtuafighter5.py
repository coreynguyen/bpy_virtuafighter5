"""    ======================================================================

    Python Code:    [PS3] Virtua Fighter 5 (for Blender 2.91.2)
    Author:         mariokart64n
    Date:           February 23, 2021
    Version:        0.1

    ======================================================================

    Credits:
        Junkoenoshima        supplying for files
                                https://www.deviantart.com/hallowedgal

        Chrrox                previous work on format
                                https://www.deviantart.com/chrrox
                                https://forum.xentax.com/viewtopic.php?f=16&t=5484

    ======================================================================

    Known Issues:
        Parenting from import is missing or broken

    ======================================================================

    ChangeLog:

    2021-01-31
        Script Wrote

    2021-02-15
        added a batch import feature to import many parts at once
        fixed issue with strip reading function skipping faces
        fixed materials by fixing txp reader which was not indexing with cubemaps
        tweaked material assignment
        added bone tools to assit with parenting the bones
        added fixed texture paths to load images automatically

    2021-02-23
        MaxScript was ported over to blender v2.91.2
    
    2021-03-02
        patched in support for the 2nd UV channel 2

    ====================================================================== """

import bpy  # Needed to interface with blender
from bpy_extras.io_utils import ImportHelper  # needed for OT_TestOpenFilebrowser
import struct  # Needed for Binary Reader
import random
import math
from pathlib import Path  # Needed for os stuff

useOpenDialog = True

#
# ====================================================================================
# MAXCSRIPT FUNCTIONS
# ====================================================================================
# These function are written to mimic native functions in
# maxscript. This is to make porting my old maxscripts
# easier, so alot of these functions may be redundant..
# ====================================================================================
#

signed, unsigned = 0, 1  # Enums for read function
seek_set, seek_cur, seek_end = 0, 1, 2  # Enums for seek function


def cross(vec1=(0.0, 0.0, 0.0), vec2=(0.0, 0.0, 0.0)):
    return (
        vec2[1] * vec1[2] - vec2[2] * vec1[1],
        vec2[2] * vec1[0] - vec2[0] * vec1[2],
        vec2[0] * vec1[1] - vec2[1] * vec1[0]
    )


def dot(a=(0.0, 0.0, 0.0), b=(0.0, 0.0, 0.0)):
    return sum(map(lambda pair: pair[0] * pair[1], zip(a, b)))


def abs(val=0.0):
    # return (-val if val < 0 else val)
    return math.abs(val)


def sqrt(n=0.0, l=0.001):
    # x = n
    # root = 0.0
    # count = 0
    # while True:
    #    count += 1
    #    if x == 0: break
    #    root = 0.5 * (x + (n / x))
    #    if abs(root - x) < l: break
    #    x = root
    # return root
    return math.sqrt(n)


def normalize(vec=(0.0, 0.0, 0.0)):
    div = sqrt((vec[0] * vec[0]) + (vec[1] * vec[1]) + (vec[2] * vec[2]))
    return (
        (vec[0] / div) if vec[0] != 0 else 0.0,
        (vec[1] / div) if vec[1] != 0 else 0.0,
        (vec[2] / div) if vec[2] != 0 else 0.0
    )


def distance(vec1=(0.0, 0.0, 0.0), vec2=(0.0, 0.0, 0.0)):
    return (sqrt((pow(vec2[0] - vec1[0], 2)) + (pow(vec2[1] - vec1[1], 2)) + (pow(vec2[2] - vec1[2], 2))))


def radToDeg(radian):
    # return (radian * 57.2957795130823208767981548141)
    return math.degrees(radian)


def degToRad(degree):
    # return (degree * 0.0174532925199432957692369076849)
    return math.radians(degree)


def bit():
    def And(integer1, integer2): return (integer1 & integer2)

    def Or(integer1, integer2): return (integer1 | integer2)

    def Xor(integer1, integer2): return (integer1 ^ integer2)

    def Not(integer1): return (~integer1)

    def Get(integer1, integer2): return ((integer1 & (1 << integer2)) >> integer2)

    def Set(integer1, integer2, boolean): return (
            integer1 ^ ((integer1 * 0 - (int(boolean))) ^ integer1) & ((integer1 * 0 + 1) << integer2))

    def Shift(integer1, integer2): return ((integer1 >> -integer2) if integer2 < 0 else (integer1 << integer2))

    def CharAsInt(string): return ord(str(integer))

    def IntAsChar(integer): return chr(int(integer))

    def IntAsHex(integer): return format(integer, 'X')

    def IntAsFloat(integer): return struct.unpack('f', integer.to_bytes(4, byteorder='little'))


class matrix3:
    row1 = [1.0, 0.0, 0.0]
    row2 = [0.0, 1.0, 0.0]
    row3 = [0.0, 0.0, 1.0]
    row4 = [0.0, 0.0, 0.0]

    def __init__(self, rowA=[1.0, 0.0, 0.0], rowB=[0.0, 1.0, 0.0], rowC=[0.0, 0.0, 1.0], rowD=[0.0, 0.0, 0.0]):
        self.row1 = rowA
        self.row2 = rowB
        self.row3 = rowC
        self.row4 = rowD

    def __repr__(self):
        return (
                "matrix3([" + str(self.row1[0]) +
                ", " + str(self.row1[1]) +
                ", " + str(self.row1[2]) +
                "], [" + str(self.row2[0]) +
                ", " + str(self.row2[1]) +
                ", " + str(self.row2[2]) +
                "], [" + str(self.row3[0]) +
                ", " + str(self.row3[1]) +
                ", " + str(self.row3[2]) +
                "], [" + str(self.row4[0]) +
                ", " + str(self.row4[1]) +
                ", " + str(self.row4[2]) + "])"
        )

    def asMat3(self):
        return (
            (self.row1[0], self.row1[1], self.row1[2]),
            (self.row2[0], self.row2[1], self.row2[2]),
            (self.row3[0], self.row3[1], self.row3[2]),
            (self.row4[0], self.row4[1], self.row4[2])
        )

    def asMat4(self):
        return (
            (self.row1[0], self.row1[1], self.row1[2], 0.0),
            (self.row2[0], self.row2[1], self.row2[2], 0.0),
            (self.row3[0], self.row3[1], self.row3[2], 0.0),
            (self.row4[0], self.row4[1], self.row4[2], 1.0)
        )

    def inverse(self):
        row1_3 = 0.0
        row2_3 = 0.0
        row3_3 = 0.0
        row4_3 = 1.0
        inv = [float] * 16
        inv[0] = (self.row2[1] * self.row3[2] * row4_3 -
                  self.row2[1] * row3_3 * self.row4[2] -
                  self.row3[1] * self.row2[2] * row4_3 +
                  self.row3[1] * row2_3 * self.row4[2] +
                  self.row4[1] * self.row2[2] * row3_3 -
                  self.row4[1] * row2_3 * self.row3[2])
        inv[4] = (-self.row2[0] * self.row3[2] * row4_3 +
                  self.row2[0] * row3_3 * self.row4[2] +
                  self.row3[0] * self.row2[2] * row4_3 -
                  self.row3[0] * row2_3 * self.row4[2] -
                  self.row4[0] * self.row2[2] * row3_3 +
                  self.row4[0] * row2_3 * self.row3[2])
        inv[8] = (self.row2[0] * self.row3[1] * row4_3 -
                  self.row2[0] * row3_3 * self.row4[1] -
                  self.row3[0] * self.row2[1] * row4_3 +
                  self.row3[0] * row2_3 * self.row4[1] +
                  self.row4[0] * self.row2[1] * row3_3 -
                  self.row4[0] * row2_3 * self.row3[1])
        inv[12] = (-self.row2[0] * self.row3[1] * self.row4[2] +
                   self.row2[0] * self.row3[2] * self.row4[1] +
                   self.row3[0] * self.row2[1] * self.row4[2] -
                   self.row3[0] * self.row2[2] * self.row4[1] -
                   self.row4[0] * self.row2[1] * self.row3[2] +
                   self.row4[0] * self.row2[2] * self.row3[1])
        inv[1] = (-self.row1[1] * self.row3[2] * row4_3 +
                  self.row1[1] * row3_3 * self.row4[2] +
                  self.row3[1] * self.row1[2] * row4_3 -
                  self.row3[1] * row1_3 * self.row4[2] -
                  self.row4[1] * self.row1[2] * row3_3 +
                  self.row4[1] * row1_3 * self.row3[2])
        inv[5] = (self.row1[0] * self.row3[2] * row4_3 -
                  self.row1[0] * row3_3 * self.row4[2] -
                  self.row3[0] * self.row1[2] * row4_3 +
                  self.row3[0] * row1_3 * self.row4[2] +
                  self.row4[0] * self.row1[2] * row3_3 -
                  self.row4[0] * row1_3 * self.row3[2])
        inv[9] = (-self.row1[0] * self.row3[1] * row4_3 +
                  self.row1[0] * row3_3 * self.row4[1] +
                  self.row3[0] * self.row1[1] * row4_3 -
                  self.row3[0] * row1_3 * self.row4[1] -
                  self.row4[0] * self.row1[1] * row3_3 +
                  self.row4[0] * row1_3 * self.row3[1])
        inv[13] = (self.row1[0] * self.row3[1] * self.row4[2] -
                   self.row1[0] * self.row3[2] * self.row4[1] -
                   self.row3[0] * self.row1[1] * self.row4[2] +
                   self.row3[0] * self.row1[2] * self.row4[1] +
                   self.row4[0] * self.row1[1] * self.row3[2] -
                   self.row4[0] * self.row1[2] * self.row3[1])
        inv[2] = (self.row1[1] * self.row2[2] * row4_3 -
                  self.row1[1] * row2_3 * self.row4[2] -
                  self.row2[1] * self.row1[2] * row4_3 +
                  self.row2[1] * row1_3 * self.row4[2] +
                  self.row4[1] * self.row1[2] * row2_3 -
                  self.row4[1] * row1_3 * self.row2[2])
        inv[6] = (-self.row1[0] * self.row2[2] * row4_3 +
                  self.row1[0] * row2_3 * self.row4[2] +
                  self.row2[0] * self.row1[2] * row4_3 -
                  self.row2[0] * row1_3 * self.row4[2] -
                  self.row4[0] * self.row1[2] * row2_3 +
                  self.row4[0] * row1_3 * self.row2[2])
        inv[10] = (self.row1[0] * self.row2[1] * row4_3 -
                   self.row1[0] * row2_3 * self.row4[1] -
                   self.row2[0] * self.row1[1] * row4_3 +
                   self.row2[0] * row1_3 * self.row4[1] +
                   self.row4[0] * self.row1[1] * row2_3 -
                   self.row4[0] * row1_3 * self.row2[1])
        inv[14] = (-self.row1[0] * self.row2[1] * self.row4[2] +
                   self.row1[0] * self.row2[2] * self.row4[1] +
                   self.row2[0] * self.row1[1] * self.row4[2] -
                   self.row2[0] * self.row1[2] * self.row4[1] -
                   self.row4[0] * self.row1[1] * self.row2[2] +
                   self.row4[0] * self.row1[2] * self.row2[1])
        inv[3] = (-self.row1[1] * self.row2[2] * row3_3 +
                  self.row1[1] * row2_3 * self.row3[2] +
                  self.row2[1] * self.row1[2] * row3_3 -
                  self.row2[1] * row1_3 * self.row3[2] -
                  self.row3[1] * self.row1[2] * row2_3 +
                  self.row3[1] * row1_3 * self.row2[2])
        inv[7] = (self.row1[0] * self.row2[2] * row3_3 -
                  self.row1[0] * row2_3 * self.row3[2] -
                  self.row2[0] * self.row1[2] * row3_3 +
                  self.row2[0] * row1_3 * self.row3[2] +
                  self.row3[0] * self.row1[2] * row2_3 -
                  (self.row3[0] * row1_3 * self.row2[2]))
        inv[11] = (-self.row1[0] * self.row2[1] * row3_3 +
                   self.row1[0] * row2_3 * self.row3[1] +
                   self.row2[0] * self.row1[1] * row3_3 -
                   self.row2[0] * row1_3 * self.row3[1] -
                   self.row3[0] * self.row1[1] * row2_3 +
                   self.row3[0] * row1_3 * self.row2[1])
        inv[15] = (self.row1[0] * self.row2[1] * self.row3[2] -
                   self.row1[0] * self.row2[2] * self.row3[1] -
                   self.row2[0] * self.row1[1] * self.row3[2] +
                   self.row2[0] * self.row1[2] * self.row3[1] +
                   self.row3[0] * self.row1[1] * self.row2[2] -
                   self.row3[0] * self.row1[2] * self.row2[1])
        det = self.row1[0] * inv[0] + self.row1[1] * inv[4] + self.row1[2] * inv[8] + row1_3 * inv[12]
        if det != 0:
            det = 1.0 / det
            return (matrix3(
                [inv[0] * det, inv[1] * det, inv[2] * det],
                [inv[4] * det, inv[5] * det, inv[6] * det],
                [inv[8] * det, inv[9] * det, inv[10] * det],
                [inv[12] * det, inv[13] * det, inv[14] * det]
            ))
        else:
            return matrix3(self.row1, self.row2, self.row3, self.row4)

    def multiply(self, B):
        C = matrix3()
        A_row1_3, A_row2_3, A_row3_3, A_row4_3 = 0.0, 0.0, 0.0, 1.0
        # B_row1_3, B_row2_3, B_row3_3, B_row4_3 = 0.0, 0.0, 0.0, 1.0
        C.row1[0] = self.row1[0] * B.row1[0] + self.row1[1] * B.row2[0] + self.row1[2] * B.row3[0] + A_row1_3 * B.row4[
            0]
        C.row1[1] = self.row1[0] * B.row1[1] + self.row1[1] * B.row2[1] + self.row1[2] * B.row3[1] + A_row1_3 * B.row4[
            1]
        C.row1[2] = self.row1[0] * B.row1[2] + self.row1[1] * B.row2[2] + self.row1[2] * B.row3[2] + A_row1_3 * B.row4[
            2]
        # C.row1[3] = self.row1[0] * B_row1_3 + self.row1[1] * B_row2_3 + self.row1[2] * B_row3_3 + A_row1_3 * B_row4_3
        C.row2[0] = self.row2[0] * B.row1[0] + self.row2[1] * B.row2[0] + self.row2[2] * B.row3[0] + A_row2_3 * B.row4[
            0]
        C.row2[1] = self.row2[0] * B.row1[1] + self.row2[1] * B.row2[1] + self.row2[2] * B.row3[1] + A_row2_3 * B.row4[
            1]
        C.row2[2] = self.row2[0] * B.row1[2] + self.row2[1] * B.row2[2] + self.row2[2] * B.row3[2] + A_row2_3 * B.row4[
            2]
        # C.row2[3] = self.row2[0] * B_row1_3 + self.row2[1] * B_row2_3 + self.row2[2] * B_row3_3 + A_row2_3 * B_row4_3
        C.row3[0] = self.row3[0] * B.row1[0] + self.row3[1] * B.row2[0] + self.row3[2] * B.row3[0] + A_row3_3 * B.row4[
            0]
        C.row3[1] = self.row3[0] * B.row1[1] + self.row3[1] * B.row2[1] + self.row3[2] * B.row3[1] + A_row3_3 * B.row4[
            1]
        C.row3[2] = self.row3[0] * B.row1[2] + self.row3[1] * B.row2[2] + self.row3[2] * B.row3[2] + A_row3_3 * B.row4[
            2]
        # C.row3[3] = self.row3[0] * B_row1_3 + self.row3[1] * B_row2_3 + self.row3[2] * B_row3_3 + A_row3_3 * B_row4_3
        C.row4[0] = self.row4[0] * B.row1[0] + self.row4[1] * B.row2[0] + self.row4[2] * B.row3[0] + A_row4_3 * B.row4[
            0]
        C.row4[1] = self.row4[0] * B.row1[1] + self.row4[1] * B.row2[1] + self.row4[2] * B.row3[1] + A_row4_3 * B.row4[
            1]
        C.row4[2] = self.row4[0] * B.row1[2] + self.row4[1] * B.row2[2] + self.row4[2] * B.row3[2] + A_row4_3 * B.row4[
            2]
        # C.row4[3] = self.row4[0] * B_row1_3 + self.row4[1] * B_row2_3 + self.row4[2] * B_row3_3 + A_row4_3 * B_row4_3
        return C


class skinOps:
    mesh = None
    skin = None
    armature = None

    def __init__(self, meshObj, armObj, skinName="Skin"):
        self.mesh = meshObj
        self.armature = armObj
        if self.mesh != None:
            for m in self.mesh.modifiers:
                if m.type == "ARMATURE":
                    self.skin = m
                    break
            if self.skin == None:
                self.skin = self.mesh.modifiers.new(type="ARMATURE", name=skinName)
            self.skin.use_vertex_groups = True
            self.skin.object = self.armature
            self.mesh.parent = self.armature

    def addbone(self, boneName, update_flag = 0):
        # Adds a bone to the vertex group list
        #print("boneName:\t%s" % boneName)
        vertGroup = self.mesh.vertex_groups.get(boneName)
        if not vertGroup:
            self.mesh.vertex_groups.new(name=boneName)
        return None

    def NormalizeWeights(self, weight_array, roundTo=0):
        # Makes All weights in the weight_array sum to 1.0
        # Set roundTo 0.01 to limit weight; 0.33333 -> 0.33
        n = []
        if len(weight_array) > 0:
            s = 0.0
            n = [float] * len(weight_array)
            for i in range(0, len(weight_array)):
                if roundTo != 0:
                    n[i] = (float(int(weight_array[i] * (1.0 / roundTo)))) / (1.0 / roundTo)
                else:
                    n[i] = weight_array[i]
                s += n[i]
            s = 1.0 / s
            for i in range(0, len(weight_array)):
                n[i] *= s
        return n
    
    def GetNumberBones(self):
        # Returns the number of bones present in the vertex group list
        num = 0
        for b in self.armature.data.bones:
            if self.mesh.vertex_groups.get(b.name):
                num += 1
        return num

    def GetNumberVertices(self):
        # Returns the number of vertices for the object the Skin modifier is applied to.
        return len(self.mesh.data.vertices)

    def ReplaceVertexWeights(self, vertex_integer, vertex_bone_array, weight_array):
        # Sets the influence of the specified bone(s) to the specified vertex.
        # Any influence weights for the bone(s) that are not specified are erased.
        # If the bones and weights are specified as arrays, the arrays must be of the same size.

        # Check that both arrays match
        numWeights = len(vertex_bone_array)
        if len(weight_array) == numWeights and numWeights > 0:
            
            # Erase Any Previous Weight
            for g in self.mesh.data.vertices[vertex_integer].groups:
                self.mesh.vertex_groups[g.index].add([vertex_integer], 0.0, 'REPLACE')

            # Add New Weights
            for i in range(0, numWeights):
                self.mesh.vertex_groups[vertex_bone_array[i]].add([vertex_integer], weight_array[i], 'REPLACE')
            return True
        return False

    def GetVertexWeightCount(self, vertex_integer):
        # Returns the number of bones (vertex groups) influencing the specified vertex.
        num = 0
        for g in self.mesh.vertices[vertex_integer].groups:
            # need to write more crap
            # basically i need to know if the vertex group is for a bone and is even label as deformable
            # but lzy, me fix l8tr
            num += 1
        return num

    def boneAffectLimit(self, limit):
        # Reduce the number of bone influences affecting a single vertex
        # I copied and pasted busted ass code from somewhere as an example to
        # work from... still need to write this out but personally dont have a
        # need for it
        # for v in self.mesh.vertices:

        #     # Get a list of the non-zero group weightings for the vertex
        #     nonZero = []
        #     for g in v.groups:

        #         g.weight = round(g.weight, 4)

        #         if g.weight & lt; .0001:
        #             continue

        #         nonZero.append(g)

        #     # Sort them by weight decending
        #     byWeight = sorted(nonZero, key=lambda group: group.weight)
        #     byWeight.reverse()

        #     # As long as there are more than 'maxInfluence' bones, take the lowest influence bone
        #     # and distribute the weight to the other bones.
        #     while len(byWeight) & gt; limit:

        #         #print("Distributing weight for vertex %d" % (v.index))

        #         # Pop the lowest influence off and compute how much should go to the other bones.
        #         minInfluence = byWeight.pop()
        #         distributeWeight = minInfluence.weight / len(byWeight)
        #         minInfluence.weight = 0

        #         # Add this amount to the other bones
        #         for influence in byWeight:
        #             influence.weight = influence.weight + distributeWeight

        #         # Round off the remaining values.
        #         for influence in byWeight:
        #             influence.weight = round(influence.weight, 4)
        return None

    def GetVertexWeightBoneID(self, vertex_integer, vertex_bone_integer):
        # Returns the vertex group index of the Nth bone affecting the specified vertex.

        return None

    def GetVertexWeight(self, vertex_integer, vertex_bone_integer):
        # Returns the influence of the Nth bone affecting the specified vertex.
        for v in msh.data.vertices:  # <MeshVertex>                              https://docs.blender.org/api/current/bpy.types.MeshVertex.html
            weights = [g.weight for g in v.groups]
            boneids = [g.group for g in v.groups]
        # return [vert for vert in bpy.context.object.data.vertices if bpy.context.object.vertex_groups['vertex_group_name'].index in [i.group for i in vert.groups]]
        return [vert for vert in bpy.context.object.data.vertices if
                bpy.context.object.vertex_groups['vertex_group_name'].index in [i.group for i in vert.groups]]

    def GetVertexWeightByBoneName(self, vertex_bone_name):
        return [vert for vert in self.mesh.data.vertices if
                self.mesh.data.vertex_groups[vertex_bone_name].index in [i.group for i in vert.groups]]

    def GetSelectedBone(self):
        # Returns the index of the current selected bone in the Bone list.
        return self.mesh.vertex_groups.active_index

    def GetBoneName(self, bone_index, nameflag_index):
        # Returns the bone name or node name of a bone specified by ID.
        name = ""
        try:
            name = self.mesh.vertex_groups[bone_index].name
        except:
            pass
        return name

    def GetListIDByBoneID(self, BoneID_integer):
        # Returns the ListID index given the BoneID index value.
        # The VertexGroupListID index is the index into the name-sorted.
        # The BoneID index is the non-sorted index, and is the index used by other methods that require a bone index.
        index = -1
        try:
            index = self.mesh.vertex_groups[self.armature.data.bones[BoneID_integer]].index
        except:
            pass
        return index

    def GetBoneIDByListID(self, bone_index):
        # Returns the BoneID index given the ListID index value. The ListID index is the index into the name-sorted bone listbox.
        # The BoneID index is the non-sorted index, and is the index used by other methods that require a bone index
        index = -1
        try:
            index = self.armature.data.bones[self.mesh.vertex_groups[bone_index].name].index
        except:
            pass
        return index

    def weightAllVertices(self):
        # Ensure all weights have weight and that are equal to a sum of 1.0
        return None

    def clearZeroWeights(self, limit=0.0):
        # Removes weights that are a threshold
        # for v in self.mesh.vertices:
        #     nonZero = []
        #     for g in v.groups:

        #         g.weight = round(g.weight, 4)

        #         if g.weight & le; limit:
        #             continue

        #         nonZero.append(g)

        #     # Sort them by weight decending
        #     byWeight = sorted(nonZero, key=lambda group: group.weight)
        #     byWeight.reverse()

        #     # As long as there are more than 'maxInfluence' bones, take the lowest influence bone
        #     # and distribute the weight to the other bones.
        #     while len(byWeight) & gt; limit:

        #         #print("Distributing weight for vertex %d" % (v.index))

        #         # Pop the lowest influence off and compute how much should go to the other bones.
        #         minInfluence = byWeight.pop()
        #         distributeWeight = minInfluence.weight / len(byWeight)
        #         minInfluence.weight = 0

        #         # Add this amount to the other bones
        #         for influence in byWeight:
        #             influence.weight = influence.weight + distributeWeight

        #         # Round off the remaining values.
        #         for influence in byWeight:
        #             influence.weight = round(influence.weight, 4)
        return None

    def SelectBone(self, bone_integer):
        # Selects the specified bone in the Vertex Group List
        self.mesh.vertex_groups.active_index = bone_integer
        return None

    # Probably wont bother writing this unless I really need this ability
    def saveEnvelope(self):
        # Saves Weight Data to an external binary file
        return None

    def saveEnvelopeAsASCII(self):
        # Saves Weight Data to an external ASCII file
        envASCII = "ver 3\n"
        envASCII = "numberBones " + str(self.GetNumberBones()) + "\n"
        num = 0
        for b in self.armature.data.bones:
            if self.mesh.vertex_groups.get(b.name):
                envASCII += "[boneName] " + b.name + "\n"
                envASCII += "[boneID] " + str(num) + "\n"
                envASCII += "  boneFlagLock 0\n"
                envASCII += "  boneFlagAbsolute 2\n"
                envASCII += "  boneFlagSpline 0\n"
                envASCII += "  boneFlagSplineClosed 0\n"
                envASCII += "  boneFlagDrawEnveloe 0\n"
                envASCII += "  boneFlagIsOldBone 0\n"
                envASCII += "  boneFlagDead 0\n"
                envASCII += "  boneFalloff 0\n"
                envASCII += "  boneStartPoint 0.000000 0.000000 0.000000\n"
                envASCII += "  boneEndPoint 0.000000 0.000000 0.000000\n"
                envASCII += "  boneCrossSectionCount 2\n"
                envASCII += "    boneCrossSectionInner0 3.750000\n"
                envASCII += "    boneCrossSectionOuter0 13.125000\n"
                envASCII += "    boneCrossSectionU0 0.000000\n"
                envASCII += "    boneCrossSectionInner1 3.750000\n"
                envASCII += "    boneCrossSectionOuter1 13.125000\n"
                envASCII += "    boneCrossSectionU1 1.000000\n"
                num += 1
        envASCII += "[Vertex Data]\n"
        envASCII += "  nodeCount 1\n"
        envASCII += "  [baseNodeName] " + self.mesh.name + "\n"
        envASCII += "    vertexCount " + str(len(self.mesh.vertices)) + "\n"
        for v in self.mesh.vertices:
            envASCII += "    [vertex" + str(v.index) + "]\n"
            envASCII += "      vertexIsModified 0\n"
            envASCII += "      vertexIsRigid 0\n"
            envASCII += "      vertexIsRigidHandle 0\n"
            envASCII += "      vertexIsUnNormalized 0\n"
            envASCII += "      vertexLocalPosition 0.000000 0.000000 24.38106\n"
            envASCII += "      vertexWeightCount " + str(len(v.groups)) + "\n"
            envASCII += "      vertexWeight "
            for g in v.groups:
                envASCII += str(g.group) + ","
                envASCII += str(g.weight) + " "
            envASCII += "      vertexSplineData 0.000000 0 0 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000   "
        envASCII += "  numberOfExclusinList 0\n"
        return envASCII

    def loadEnvelope(self):
        # Imports Weight Data to an external Binary file
        return None

    def loadEnvelopeAsASCII(self):
        # Imports Weight Data to an external ASCII file
        return None


class boneSys:
    armature = None
    layer = None

    def __init__(self, armatureName="Skeleton", layerName="", rootName="Scene Root"):

        # Clear Any Object Selections
        # for o in bpy.context.selected_objects: o.select = False
        bpy.context.view_layer.objects.active = None

        # Get Collection (Layers)
        if self.layer == None:
            if layerName != "":
                # make collection
                self.layer = bpy.data.collections.new(layerName)
                bpy.context.scene.collection.children.link(self.layer)
            else:
                self.layer = bpy.data.collections[bpy.context.view_layer.active_layer_collection.name]

        # Check for Armature
        armName = armatureName
        if armatureName == "": armName = "Skeleton"
        self.armature = bpy.context.scene.objects.get(armName)

        if self.armature == None:
            # Create Root Bone
            root = bpy.data.armatures.new(rootName)
            root.name = rootName

            # Create Armature
            self.armature = bpy.data.objects.new(armName, root)
            self.layer.objects.link(self.armature)

        self.armature.display_type = 'WIRE'
        self.armature.show_in_front = True

    def editMode(self, enable=True):
        #
        # Data Pointers Seem to get arranged between
        # Entering and Exiting EDIT Mode, which is
        # Required to make changes to the bones
        #
        # This needs to be called beofre and after making changes
        #

        if enable:
            # Clear Any Object Selections
            bpy.context.view_layer.objects.active = None

            # Set Armature As Active Selection
            if bpy.context.view_layer.objects.active != self.armature:
                bpy.context.view_layer.objects.active = self.armature

            # Switch to Edit Mode
            if bpy.context.object.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        else:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        return None

        def count(self):
            return len(self.armature.data.bones)

    def getNodeByName(self, boneName):
        # self.editMode(True)
        node = None
        try:
            # node = self.armature.data.bones.get('boneName')
            node = self.armature.data.edit_bones[boneName]
        except:
            pass
        # self.editMode(False)
        return node

    def getChildren(self, boneName):
        childs = []
        b = self.getNodeByName(boneName)
        if b != None:
            for bone in self.armature.data.edit_bones:
                if bone.parent == b: childs.append(bone)
        return childs

    def setParent(self, boneName, parentName):
        b = self.getNodeByName(boneName)
        p = self.getNodeByName(parentName)
        if b != None and p != None:
            b.parent = p
            return True
        return False

    def getParent(self, boneName):
        par = None
        b = self.getNodeByName(boneName)
        if b != None: par = b.parent
        return par

    def getPosition(self, boneName):
        position = (0.0, 0.0, 0.0)
        b = self.getNodeByName(boneName)
        if b != None:
            position = (
                self.armature.location[0] + b.head[0],
                self.armature.location[1] + b.head[1],
                self.armature.location[2] + b.head[2],
            )
        return position

    def setPosition(self, boneName, position):
        b = self.getNodeByName(boneName)
        pos = (
            position[0] - self.armature.location[0],
            position[1] - self.armature.location[1],
            position[2] - self.armature.location[2]
            )
        if b != None and distance(b.tail, pos) > 0.0000001: b.head = pos
        return None

    def getEndPosition(self, boneName):
        position = (0.0, 0.0, 0.0)
        b = self.getNodeByName(boneName)
        if b != None:
            position = (
                self.armature.location[0] + b.tail[0],
                self.armature.location[1] + b.tail[1],
                self.armature.location[2] + b.tail[2],
            )
        return position

    def setEndPosition(self, boneName, position):
        b = self.getNodeByName(boneName)
        pos = (
            position[0] - self.armature.location[0],
            position[1] - self.armature.location[1],
            position[2] - self.armature.location[2]
            )
        if b != None and distance(b.head, pos) > 0.0000001: b.tail = pos
        return None

    def setUserProp(self, boneName, key_string, value):
        b = self.getNodeByName(boneName)
        try:
            if b != None: b[key_string] = value
            return True
        except:
            return False

    def getUserProp(self, boneName, key_string):
        value = None
        b = self.getNodeByName(boneName)
        if b != None:
            try:
                value = b[key_string]
            except:
                pass
        return value

    def setTransform(self, boneName,
                     matrix=((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (1.0, 0.0, 0.0, 1.0))):
        b = self.getNodeByName(boneName)
        if b != None:
            b.matrix = matrix
            return True
        return False

    def setVisibility(self, boneName, visSet=(
            True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
            False,
            False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
            False)):
        # Assign Visible Layers
        if b != None:
            b.layers = visSet
            return True
        return False

    def setBoneGroup(self, boneName, normalCol=(0.0, 0.0, 0.0), selctCol=(0.0, 0.0, 0.0), activeCol=(0.0, 0.0, 0.0)):
        # Create Bone Group (custom bone colours ??)
        b = self.getNodeByName(boneName)
        if b != None:
            # arm = bpy.data.objects.new("Armature", bpy.data.armatures.new("Skeleton"))
            # layer.objects.link(arm)
            # obj.parent = arm
            # bgrp = self.armature.pose.bone_groups.new(name=msh.name)
            # bgrp.color_set = 'CUSTOM'
            # bgrp.colors.normal = normalCol
            # bgrp.colors.select = selctCol
            # bgrp.colors.active = activeCol
            # for b in obj.vertex_groups.keys():
            #    self.armature.pose.bones[b].bone_group = bgrp
            return True
        return False

    def createBone(self, boneName="", startPos=(0.0, 0.0, 0.0), endPos=(0.0, 0.0, 1.0), zAxis=(1.0, 0.0, 0.0)):

        self.editMode(True)

        # Check if bone exists
        b = None
        if boneName != "":
            try:
                b = self.armature.data.edit_bones[boneName]
                return False
            except:
                pass

        if b == None:

            # Generate Bone Name
            bName = boneName
            if bName == "": bName = "Bone_" + '{:04d}'.format(len(self.armature.data.edit_bones))

            # Create Bone
            b = self.armature.data.edit_bones.new(bName)
            b.name = bName

            # Set As Deform Bone
            b.use_deform = True

            # Set Rotation
            roll, pitch, yaw = 0.0, 0.0, 0.0
            try:
                roll = math.acos((dot(zAxis, (1, 0, 0))) / (
                        math.sqrt(((pow(zAxis[0], 2)) + (pow(zAxis[1], 2)) + (pow(zAxis[2], 2)))) * 1.0))
            except:
                pass
            try:
                pitch = math.acos((dot(zAxis, (0, 1, 0))) / (
                        math.sqrt(((pow(zAxis[0], 2)) + (pow(zAxis[1], 2)) + (pow(zAxis[2], 2)))) * 1.0))
            except:
                pass
            try:
                yaw = math.acos((dot(zAxis, (0, 0, 1))) / (
                        math.sqrt(((pow(zAxis[0], 2)) + (pow(zAxis[1], 2)) + (pow(zAxis[2], 2)))) * 1.0))
            except:
                pass

            su = math.sin(roll)
            cu = math.cos(roll)
            sv = math.sin(pitch)
            cv = math.cos(pitch)
            sw = math.sin(yaw)
            cw = math.cos(yaw)

            b.matrix = (
                (cv * cw, su * sv * cw - cu * sw, su * sw + cu * sv * cw, 0.0),
                (cv * sw, cu * cw + su * sv * sw, cu * sv * sw - su * cw, 0.0),
                (-sv, su * cv, cu * cv, 0.0),
                (startPos[0], startPos[1], startPos[2], 1.0)
            )

            # Set Length (has to be larger then 0.1?)
            b.length = 1.0
            if startPos != endPos:
                b.head = startPos
                b.tail = endPos

        # Exit Edit Mode
        self.editMode(False)

        return True


def messageBox(message="", title="Message Box", icon='INFO'):
    def draw(self, context): self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    return None


def getNodeByName(nodeName):
    return bpy.context.scene.objects.get(nodeName)


def classof(nodeObj):
    try:
        return str(nodeObj.type)
    except:
        return None


def makeDir(folderName):
    return Path(folderName).mkdir(parents=True, exist_ok=True)


def setUserProp(node, key_string, value):
    try:
        node[key_string] = value
        return True
    except:
        return False


def getUserProp(node, key_string):
    value = None
    try:
        value = node[key_string]
    except:
        pass
    return value


def getFileSize(filename):
    return Path(filename).stat().st_size


def doesFileExist(filename):
    file = Path(filename)
    if file.is_file():
        return True
    elif file.is_dir():
        return True
    else:
        return False


def clearListener(len=64):
    for i in range(0, len): print('')


def filenameFromPath(file):  # returns: "myImage.jpg"
    return Path(file).name


def getFilenamePath(file):  # returns: "g:\subdir1\subdir2\"
    return (str(Path(file).resolve().parent) + "\\")


def getFilenameFile(file):  # returns: "myImage"
    return Path(file).stem


def getFilenameType(file):  # returns: ".jpg"
    return Path(file).suffix


def toUpper(string):
    return string.upper()


def toLower(string):
    return string.upper()


def filterString(string, string_search):
    for s in enumerate(string_search):
        string.replace(s[1], string_search[0])
    return string.split(string_search[0])


def findItem(array, value):
    index = -1
    try:
        index = array.index(value)
    except:
        pass
    return index


def append(array, value):
    array.append(value)
    return None


def appendIfUnique(array, value):
    try:
        array.index(value)
    except:
        array.append(value)
    return None


class fopen:
    little_endian = True
    file = ""
    mode = 'rb'
    data = bytearray()
    size = 0
    pos = 0
    isGood = False

    def __init__(self, filename=None, mode='rb', isLittleEndian=True):
        if mode == 'rb':
            if filename != None and Path(filename).is_file():
                self.data = open(filename, mode).read()
                self.size = len(self.data)
                self.pos = 0
                self.mode = mode
                self.file = filename
                self.little_endian = isLittleEndian
                self.isGood = True
        else:
            self.file = filename
            self.mode = mode
            self.data = bytearray()
            self.pos = 0
            self.size = 0
            self.little_endian = isLittleEndian
            self.isGood = False

        return None

    # def __del__(self):
    #    self.flush()

    def resize(self, dataSize=0):
        if dataSize > 0:
            self.data = bytearray(dataSize)
        else:
            self.data = bytearray()
        self.pos = 0
        self.size = dataSize
        self.isGood = False
        return None

    def flush(self):
        print("flush")
        print("file:\t%s" % self.file)
        print("isGood:\t%s" % self.isGood)
        print("size:\t%s" % len(self.data))
        if self.file != "" and not self.isGood and len(self.data) > 0:
            self.isGood = True

            s = open(self.file, 'w+b')
            s.write(self.data)
            s.close()

    def read_and_unpack(self, unpack, size):
        '''
          Charactor, Byte-order
          @,         native, native
          =,         native, standard
          <,         little endian
          >,         big endian
          !,         network

          Format, C-type,         Python-type, Size[byte]
          c,      char,           byte,        1
          b,      signed char,    integer,     1
          B,      unsigned char,  integer,     1
          h,      short,          integer,     2
          H,      unsigned short, integer,     2
          i,      int,            integer,     4
          I,      unsigned int,   integer,     4
          f,      float,          float,       4
          d,      double,         float,       8
        '''
        value = 0
        if self.size > 0 and self.pos + size < self.size:
            value = struct.unpack_from(unpack, self.data, self.pos)[0]
            self.pos += size
        return value

    def pack_and_write(self, pack, size, value):
        if self.pos + size > self.size:
            self.data.extend(b'\x00' * ((self.pos + size) - self.size))
            self.size = self.pos + size
        try:
            struct.pack_into(pack, self.data, self.pos, value)
        except:
            print('Pos:\t%i / %i (buf:%i) [val:%i:%i:%s]' % (self.pos, self.size, len(self.data), value, size, pack))
            pass
        self.pos += size
        return None

    def set_pointer(self, offset):
        self.pos = offset
        return None


def fseek(bitStream, offset, dir):
    if dir == 0:
        bitStream.set_pointer(offset)
    elif dir == 1:
        bitStream.set_pointer(bitStream.pos + offset)
    elif dir == 2:
        bitStream.set_pointer(bitStream.pos - offset)
    return None


def ftell(bitStream):
    return bitStream.pos


def readByte(bitStream, isSigned=0):
    fmt = 'b' if isSigned == 0 else 'B'
    return (bitStream.read_and_unpack(fmt, 1))


def readShort(bitStream, isSigned=0):
    fmt = '>' if not bitStream.little_endian else '<'
    fmt += 'h' if isSigned == 0 else 'H'
    return (bitStream.read_and_unpack(fmt, 2))


def readLong(bitStream, isSigned=0):
    fmt = '>' if not bitStream.little_endian else '<'
    fmt += 'i' if isSigned == 0 else 'I'
    return (bitStream.read_and_unpack(fmt, 4))


def readLongLong(bitStream, isSigned=0):
    fmt = '>' if not bitStream.little_endian else '<'
    fmt += 'q' if isSigned == 0 else 'Q'
    return (bitStream.read_and_unpack(fmt, 8))


def readFloat(bitStream):
    fmt = '>f' if not bitStream.little_endian else '<f'
    return (bitStream.read_and_unpack(fmt, 4))


def readDouble(bitStream):
    fmt = '>d' if not bitStream.little_endian else '<d'
    return (bitStream.read_and_unpack(fmt, 8))


def readHalf(bitStream):
    uint16 = bitStream.read_and_unpack('>H' if not bitStream.little_endian else '<H', 2)
    uint32 = (
            (((uint16 & 0x03FF) << 0x0D) | ((((uint16 & 0x7C00) >> 0x0A) + 0x70) << 0x17)) |
            (((uint16 >> 0x0F) & 0x00000001) << 0x1F)
    )
    return struct.unpack('f', struct.pack('I', uint32))[0]


def readString(bitStream, length=0):
    string = ''
    pos = bitStream.pos
    lim = length if length != 0 else bitStream.size - bitStream.pos
    for i in range(0, lim):
        b = bitStream.read_and_unpack('B', 1)
        if b != 0:
            string += chr(b)
        else:
            if length > 0:
                bitStream.set_pointer(pos + length)
            break
    return string


def writeByte(bitStream, value):
    bitStream.pack_and_write('B', 1, int(value))
    return None


def writeShort(bitStream, value):
    fmt = '>H' if not bitStream.little_endian else '<H'
    bitStream.pack_and_write(fmt, 2, int(value))
    return None


def writeLong(bitStream, value):
    fmt = '>I' if not bitStream.little_endian else '<I'
    bitStream.pack_and_write(fmt, 4, int(value))
    return None


def writeFloat(bitStream, value):
    fmt = '>f' if not bitStream.little_endian else '<f'
    bitStream.pack_and_write(fmt, 4, value)
    return None


def writeLongLong(bitStream, value):
    fmt = '>Q' if not bitStream.little_endian else '<Q'
    bitStream.pack_and_write(fmt, 8, value)
    return None


def writeDoube(bitStream, value):
    fmt = '>d' if not bitStream.little_endian else '<d'
    bitStream.pack_and_write(fmt, 8, value)
    return None


def writeString(bitStream, string, length=0):
    strLen = len(string)
    if length == 0: length = strLen + 1
    for i in range(0, length):
        if i < strLen:
            bitStream.pack_and_write('b', 1, ord(string[i]))
        else:
            bitStream.pack_and_write('B', 1, 0)
    return None


def mesh(vertices=[], faces=[], materialIDs=[], tverts=[], normals=[], colours=[], materials=[], mscale=1.0,
         flipAxis=False, obj_name="Object", lay_name=''):
    #
    # This function is pretty, ugly
    # imports the mesh into blender
    #

    # Clear Any Object Selections
    # for o in bpy.context.selected_objects: o.select = False
    bpy.context.view_layer.objects.active = None

    # Get Collection (Layers)
    if lay_name != '':
        # make collection
        layer = bpy.data.collections.new(lay_name)
        bpy.context.scene.collection.children.link(layer)
    else:
        layer = bpy.data.collections[bpy.context.view_layer.active_layer_collection.name]

    # make mesh
    msh = bpy.data.meshes.new('Mesh')

    # msh.name = msh.name.replace(".", "_")

    # Apply vertex scaling
    # mscale *= bpy.context.scene.unit_settings.scale_length
    if len(vertices) > 0:
        vertArray = [[float] * 3] * len(vertices)
        if flipAxis:
            for v in range(0, len(vertices)):
                vertArray[v] = (
                    vertices[v][0] * mscale,
                    -vertices[v][2] * mscale,
                    vertices[v][1] * mscale
                )
        else:
            for v in range(0, len(vertices)):
                vertArray[v] = (
                    vertices[v][0] * mscale,
                    vertices[v][1] * mscale,
                    vertices[v][2] * mscale
                )

    # assign data from arrays
    msh.from_pydata(vertArray, [], faces)

    # set surface to smooth
    msh.polygons.foreach_set("use_smooth", [True] * len(msh.polygons))

    # Set Normals
    if len(faces) > 0:
        if len(normals) > 0:
            msh.use_auto_smooth = True
            if len(normals) == (len(faces) * 3):
                msh.normals_split_custom_set(normals)
            else:
                normArray = [[float] * 3] * (len(faces) * 3)
                if flipAxis:
                    for i in range(0, len(faces)):
                        for v in range(0, 3):
                            normArray[(i * 3) + v] = (
                                [normals[faces[i][v]][0],
                                 -normals[faces[i][v]][2],
                                 normals[faces[i][v]][1]]
                            )
                else:
                    for i in range(0, len(faces)):
                        for v in range(0, 3):
                            normArray[(i * 3) + v] = (
                                [normals[faces[i][v]][0],
                                 normals[faces[i][v]][1],
                                 normals[faces[i][v]][2]]
                            )
                msh.normals_split_custom_set(normArray)

        # create texture corrdinates
        print("tverts ", len(tverts))
        # this is just a hack, i just add all the UVs into the same space <<<
        if len(tverts) > 0:
            uvw = msh.uv_layers.new()
            #if len(tverts) == (len(faces) * 3):
            #    for v in range(0, len(faces) * 3):
            #        msh.uv_layers[uvw.name].data[v].uv = tverts[v]
            #else:
            uvwArray = [[float] * 2] * len(tverts[0])
            for i in range(0, len(tverts[0])):
                uvwArray[i] = [0.0, 0.0]
            
            for v in range(0, len(tverts[0])):
                for i in range(0, len(tverts)):
                    uvwArray[v][0] += tverts[i][v][0]
                    uvwArray[v][1] += 1.0 - tverts[i][v][1]
            
            for i in range(0, len(faces)):
                for v in range(0, 3):
                    
                    msh.uv_layers[uvw.name].data[(i * 3) + v].uv = (
                        uvwArray[faces[i][v]][0],
                        uvwArray[faces[i][v]][1]
                        )

        # create vertex colours
        if len(colours) > 0:
            col = msh.vertex_colors.new()
            if len(colours) == (len(faces) * 3):
                for v in range(0, len(faces) * 3):
                    msh.vertex_colors[col.name].data[v].color = colours[v]
            else:
                colArray = [[float] * 4] * (len(faces) * 3)
                for i in range(0, len(faces)):
                    for v in range(0, 3):
                        msh.vertex_colors[col.name].data[(i * 3) + v].color = colours[faces[i][v]]
        else:
            # Use colours to make a random display
            col = msh.vertex_colors.new()
            random_col = rancol4()
            for v in range(0, len(faces) * 3):
                msh.vertex_colors[col.name].data[v].color = random_col

    # Create Face Maps?
    # msh.face_maps.new()

    # Update Mesh
    msh.update()

    # Check mesh is Valid
    if msh.validate():
        # Erase Mesh
        print("Mesh Invalid!")
        msh.user_clear()
        bpy.data.meshes.remove(msh)
        return None

    # Assign Mesh to Object
    obj = bpy.data.objects.new(obj_name, msh)
    # obj.name = obj.name.replace(".", "_")

    for i in range(0, len(materials)):

        if len(obj.material_slots) < (i + 1):
            # if there is no slot then we append to create the slot and assign
            obj.data.materials.append(materials[i])
        else:
            # we always want the material in slot[0]
            obj.material_slots[0].material = materials[i]
        # obj.active_material = obj.material_slots[i].material

    for i in range(0, len(materialIDs)):
        obj.data.polygons[i].material_index = materialIDs[i]

    # obj.data.materials.append(material)
    layer.objects.link(obj)

    # Generate a Material
    # img_name = "Test.jpg"  # dummy texture
    # mat_count = len(texmaps)

    # if mat_count == 0 and len(materialIDs) > 0:
    #    for i in range(0, len(materialIDs)):
    #        if (materialIDs[i] + 1) > mat_count: mat_count = materialIDs[i] + 1

    # Assign Material ID's
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.context.tool_settings.mesh_select_mode = [False, False, True]

    bpy.ops.object.mode_set(mode='OBJECT')
    # materialIDs

    # Redraw Entire Scene
    # bpy.context.scene.update()

    return obj


# END OF MAXSCRIPT FUNCTIONS #########################################################


#
# ====================================================================================
# BLENDER API FUNCTIONS
# ====================================================================================
# These are functions or wrappers specific with dealing with blenders API
# ====================================================================================
#


def rancol4():
    return (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), 1.0)


def rancol3():
    return (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0))


def deleteScene(include=[]):
    if len(include) > 0:
        # Exit and Interactions
        if bpy.context.view_layer.objects.active != None:
            bpy.ops.object.mode_set(mode='OBJECT')

        # Select All
        bpy.ops.object.select_all(action='SELECT')

        # Loop Through Each Selection
        for o in bpy.context.view_layer.objects.selected:
            for t in include:
                if o.type == t:
                    bpy.data.objects.remove(o, do_unlink=True)
                    break

        # De-Select All
        bpy.ops.object.select_all(action='DESELECT')
    return None


# Callback when file(s) are selected
def wrapper1_callback(fpath="", files=[], clearScene=True, impBones=False, armName="Armature", impNormals=False,
                      impColours=False,
                      impWeights=False, guessParents=False, unpack_tex=True, mscale=1.0):
    if len(files) > 0 and clearScene: deleteScene(['MESH', 'ARMATURE'])
    for file in files:
        read(
            fpath + file.name,
            impBones, armName,
            impNormals,
            impColours,
            impWeights,
            guessParents,
            unpack_tex,
            mscale
        )
    if len(files) > 0:
        messageBox("Done!")
        return True
    else:
        return False


# Wrapper that Invokes FileSelector to open files from blender
def wrapper1(reload=False):
    # Un-Register Operator
    if reload and hasattr(bpy.types, "IMPORTHELPER_OT_wrapper1"):  # print(bpy.ops.importhelper.wrapper1.idname())

        try:
            bpy.types.TOPBAR_MT_file_import.remove(
                bpy.types.Operator.bl_rna_get_subclass_py('IMPORTHELPER_OT_wrapper1').menu_func_import)
        except:
            print("Failed to Unregister2")

        try:
            bpy.utils.unregister_class(bpy.types.Operator.bl_rna_get_subclass_py('IMPORTHELPER_OT_wrapper1'))
        except:
            print("Failed to Unregister1")

    # Define Operator
    class ImportHelper_wrapper1(bpy.types.Operator):

        # Operator Path
        bl_idname = "importhelper.wrapper1"
        bl_label = "Select File"

        # Operator Properties
        # filter_glob: bpy.props.StringProperty(default='*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp', options={'HIDDEN'})
        filter_glob: bpy.props.StringProperty(default='*_obj.bin', options={'HIDDEN'}, subtype='FILE_PATH')

        # Variables
        filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # full path of selected item (path+filename)
        filename: bpy.props.StringProperty(subtype="FILE_NAME")  # name of selected item
        directory: bpy.props.StringProperty(subtype="FILE_PATH")  # directory of the selected item
        files: bpy.props.CollectionProperty(
            type=bpy.types.OperatorFileListElement)  # a collection containing all the selected items�f filenames

        # Controls
        my_int1: bpy.props.IntProperty(name="Some Integer", description="Tooltip")
        my_float1: bpy.props.FloatProperty(name="Scale", default=1.0, description="Changes Scale of the imported Mesh")
        # my_float2: bpy.props.FloatProperty(name="Some Float point", default = 0.25, min = -0.25, max = 0.5)
        my_bool1: bpy.props.BoolProperty(name="Clear Scene", default=True,
                                         description="Deletes everything in the scene prior to importing")
        my_bool2: bpy.props.BoolProperty(name="Skeleton", default=False, description="Imports Bones to an Armature")
        my_bool3: bpy.props.BoolProperty(name="Vertex Weights", default=False, description="Builds Vertex Groups")
        my_bool4: bpy.props.BoolProperty(name="Vertex Normals", default=False, description="Applies Custom Normals")
        my_bool5: bpy.props.BoolProperty(name="Vertex Colours", default=False, description="Builds Vertex Colours")
        my_bool6: bpy.props.BoolProperty(name="Guess Parents", default=False,
                                         description="Uses algorithm to Guess Bone Parenting")
        my_bool7: bpy.props.BoolProperty(name="Dump Textures", default=False,
                                         description="Writes Textures from a file pair '_tex.bin'")
        my_string1: bpy.props.StringProperty(name="", default="Armature",
                                             description="Name of Armature to Import Bones to")
        my_dropdown1: bpy.props.EnumProperty(
            name="Drop",
            items=[
                ('CLEAR', 'clear scene', 'clear scene'),
                ('ADD_CUBE', 'add cube', 'add cube'),
                ('ADD_SPHERE', 'add sphere', 'add sphere')
            ]
        )
        my_dropdown2: bpy.props.EnumProperty(
            name="Drop",
            items=[
                ('CLEAR', 'clear scene', 'clear scene'),
                ('ADD_CUBE', 'add cube', 'add cube'),
                ('ADD_SPHERE', 'add sphere', 'add sphere')
            ]
        )

        # Runs when this class OPENS
        def invoke(self, context, event):

            # Retrieve Settings
            try:
                self.filepath = bpy.types.Scene.wrapper1_filepath
            except:
                bpy.types.Scene.wrapper1_filepath = bpy.props.StringProperty(subtype="FILE_PATH")

            try:
                self.directory = bpy.types.Scene.wrapper1_directory
            except:
                bpy.types.Scene.wrapper1_directory = bpy.props.StringProperty(subtype="FILE_PATH")

            try:
                self.my_float1 = bpy.types.Scene.wrapper1_my_float1
            except:
                bpy.types.Scene.wrapper1_my_float1 = bpy.props.FloatProperty(default=1.0)

            try:
                self.my_bool1 = bpy.types.Scene.wrapper1_my_bool1
            except:
                bpy.types.Scene.wrapper1_my_bool1 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool2 = bpy.types.Scene.wrapper1_my_bool2
            except:
                bpy.types.Scene.wrapper1_my_bool2 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool3 = bpy.types.Scene.wrapper1_my_bool3
            except:
                bpy.types.Scene.wrapper1_my_bool3 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool4 = bpy.types.Scene.wrapper1_my_bool4
            except:
                bpy.types.Scene.wrapper1_my_bool4 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool5 = bpy.types.Scene.wrapper1_my_bool5
            except:
                bpy.types.Scene.wrapper1_my_bool5 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool6 = bpy.types.Scene.wrapper1_my_bool6
            except:
                bpy.types.Scene.wrapper1_my_bool6 = bpy.props.BoolProperty(default=False)

            try:
                self.my_bool7 = bpy.types.Scene.wrapper1_my_bool7
            except:
                bpy.types.Scene.wrapper1_my_bool7 = bpy.props.BoolProperty(default=False)

            try:
                self.my_string1 = bpy.types.Scene.my_string1
            except:
                bpy.types.Scene.my_string1 = bpy.props.BoolProperty(default=False)

            # Open File Browser
            # Set Properties of the File Browser
            context.window_manager.fileselect_add(self)
            context.area.tag_redraw()

            return {'RUNNING_MODAL'}

        # Runs when this Window is CANCELLED
        def cancel(self, context):
            print("run bitch")

        # Runs when the class EXITS
        def execute(self, context):

            # Save Settings
            bpy.types.Scene.wrapper1_filepath = self.filepath
            bpy.types.Scene.wrapper1_directory = self.directory
            bpy.types.Scene.wrapper1_my_float1 = self.my_float1
            bpy.types.Scene.wrapper1_my_bool1 = self.my_bool1
            bpy.types.Scene.wrapper1_my_bool2 = self.my_bool2
            bpy.types.Scene.wrapper1_my_bool3 = self.my_bool3
            bpy.types.Scene.wrapper1_my_bool4 = self.my_bool4
            bpy.types.Scene.wrapper1_my_bool5 = self.my_bool5
            bpy.types.Scene.wrapper1_my_bool6 = self.my_bool6
            bpy.types.Scene.wrapper1_my_bool7 = self.my_bool7
            bpy.types.Scene.wrapper1_my_string1 = self.my_string1

            # Run Callback
            wrapper1_callback(
                self.directory + "\\",
                self.files,
                self.my_bool1,
                self.my_bool2,
                self.my_string1,
                self.my_bool4,
                self.my_bool5,
                self.my_bool3,
                self.my_bool6,
                self.my_bool7,
                self.my_float1
            )

            return {"FINISHED"}

            # Window Settings

        def draw(self, context):

            # Set Properties of the File Browser
            # context.space_data.params.use_filter = True
            # context.space_data.params.use_filter_folder=True #to not see folders

            # Configure Layout
            # self.layout.use_property_split = True       # To Enable Align
            # self.layout.use_property_decorate = False   # No animation.

            self.layout.row().label(text="Import Settings")

            self.layout.separator()
            self.layout.row().prop(self, "my_bool1")
            self.layout.row().prop(self, "my_float1")

            box = self.layout.box()
            box.label(text="Include")
            box.prop(self, "my_bool2")
            box.prop(self, "my_bool3")
            box.prop(self, "my_bool4")
            box.prop(self, "my_bool5")

            box = self.layout.box()
            box.label(text="Misc")
            box.prop(self, "my_bool6")
            box.prop(self, "my_bool7")
            box.label(text="Import Bones To:")
            box.prop(self, "my_string1")

            self.layout.separator()

            col = self.layout.row()
            col.alignment = 'RIGHT'
            col.label(text="  Author:", icon='QUESTION')
            col.alignment = 'LEFT'
            col.label(text="mariokart64n")

            col = self.layout.row()
            col.alignment = 'RIGHT'
            col.label(text="Release:", icon='GRIP')
            col.alignment = 'LEFT'
            col.label(text="February 22, 2021")

        def menu_func_import(self, context):
            self.layout.operator("importhelper.wrapper1", text="Virtua Fighter 5 (*_obj.bin)")

    # Register Operator
    bpy.utils.register_class(ImportHelper_wrapper1)
    bpy.types.TOPBAR_MT_file_import.append(ImportHelper_wrapper1.menu_func_import)

    # Assign Shortcut key
    # bpy.context.window_manager.keyconfigs.active.keymaps["Window"].keymap_items.new('bpy.ops.text.run_script()', 'E', 'PRESS', ctrl=True, shift=False, repeat=False)

    # Call ImportHelper
    bpy.ops.importhelper.wrapper1('INVOKE_DEFAULT')


# END OF BLENDER FUNCTIONS ###########################################################


#
# ====================================================================================
# MAIN CODE
# ====================================================================================
# The actual program... honesty I should have split the code into modules <_<
# ====================================================================================
#

class cmf_bone_info:  # 64 Bytes
    BoneOff1 = 0  # goes a table of ids
    BoneOff2 = 0  # goes table of matrices
    BoneOff3 = 0  # goes string address table
    Null = 0
    BoneCount = 0
    Unk600 = []
    childIds = []
    childMatrices = []
    childStrings = []
    childStringAddrs = []

    def read_bone_buffers(self, f=fopen()):
        i = 0
        x = 0
        tmp = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if self.BoneCount > 0 and self.BoneOff1 > 0:
            fseek(f, self.BoneOff1, seek_set)
            self.childIds = [int] * self.BoneCount
            for i in range(0, self.BoneCount):
                self.childIds[i] = readLong(f, unsigned)

        if self.BoneCount > 0 and self.BoneOff2 > 0:
            fseek(f, self.BoneOff2, seek_set)
            self.childMatrices = [matrix3] * self.BoneCount
            for i in range(0, self.BoneCount):
                for x in range(0, 16): tmp[x] = readFloat(f)
                self.childMatrices[i] = matrix3(
                    ([tmp[0] + tmp[12], tmp[4] + tmp[12], tmp[8] + tmp[12]]),
                    ([tmp[1] + tmp[13], tmp[5] + tmp[13], tmp[9] + tmp[13]]),
                    ([tmp[2] + tmp[14], tmp[6] + tmp[14], tmp[10] + tmp[14]]),
                    ([tmp[3] * tmp[15], tmp[7] * tmp[15], tmp[11] * tmp[15]]))

        #                 for x = 0, 3: # (x, y, z)
        #                     self.childMatrices[i].row1[x] = readFloat(f)
        #                     self.childMatrices[i].row2[x] = readFloat(f)
        #                     self.childMatrices[i].row3[x] = readFloat(f)
        #                     self.childMatrices[i].row4[x] = readFloat(f)
        #                     print self.childMatrices[i]
        #                     )
        #                 self.childMatrices[i].row1 += readFloat(f)
        #                 self.childMatrices[i].row2 += readFloat(f)
        #                 self.childMatrices[i].row3 += readFloat(f)
        #                 self.childMatrices[i].row4 *= readFloat(f)

        if self.BoneCount > 0 and self.BoneOff3 > 0:
            fseek(f, self.BoneOff3, seek_set)
            self.childStringAddrs = [int] * self.BoneCount
            for i in range(0, self.BoneCount):
                self.childStringAddrs[i] = readLong(f, unsigned)

            self.childStrings = [str] * self.BoneCount
            for i in range(0, self.BoneCount):
                fseek(f, self.childStringAddrs[i], seek_set)
                self.childStrings[i] = readString(f)

    def read_bone_info(self, f=fopen()):
        self.BoneOff1 = readLong(f)
        self.BoneOff2 = readLong(f)
        self.BoneOff3 = readLong(f)
        self.Null = readLong(f)
        self.BoneCount = readLong(f)
        self.Unk600 = []
        self.Unk600 = [int] * 44
        i = 0
        for i in range(0, 44):
            self.Unk600[i] = readByte(f, unsigned)


class mesh_mat_tex:  # 120 Bytes
    Unk500 = 0
    Unk501 = 0
    Unk502 = 0
    Unk503 = 0
    Unk504 = 0  # ID? if this is -1 then the texture is not used
    Unk505 = 0  # Type: 0xF0=? 0xF1=Diffuse 0xF2=Normal 0xF3=Specular
    Unk506 = [0.0, 0.0, 0.0]
    Unk507 = matrix3()
    Unk508 = 0
    Unk509 = 0
    Unk510 = 0
    Unk511 = 0
    Unk512 = 0
    Unk513 = 0
    Unk514 = 0
    Unk515 = 0

    def read_mat_tex(self, f=fopen()):
        self.Unk500 = readByte(f, unsigned)
        self.Unk501 = readByte(f, unsigned)
        self.Unk502 = readByte(f, unsigned)
        self.Unk503 = readByte(f, unsigned)
        self.Unk504 = readLong(f, signed)
        self.Unk505 = readLong(f, unsigned)
        self.Unk506 = [readFloat(f), readFloat(f), readFloat(f)]
        self.Unk507 = matrix3()
        self.Unk507.row1 = [readFloat(f), readFloat(f), readFloat(f)]
        readFloat(f)
        self.Unk507.row2 = [readFloat(f), readFloat(f), readFloat(f)]
        readFloat(f)
        self.Unk507.row3 = [readFloat(f), readFloat(f), readFloat(f)]
        readFloat(f)
        self.Unk507.row4 = [readFloat(f), readFloat(f), readFloat(f)]
        readFloat(f)
        self.Unk508 = readLong(f, unsigned)
        self.Unk509 = readLong(f, unsigned)
        self.Unk510 = readLong(f, unsigned)
        self.Unk511 = readLong(f, unsigned)
        self.Unk512 = readLong(f, unsigned)
        self.Unk513 = readLong(f, unsigned)
        self.Unk514 = readLong(f, unsigned)
        self.Unk515 = readLong(f, unsigned)


class cmf_mesh_mat:  # 1200 Bytes
    Unk400 = 0
    Unk401 = 0
    Mattype = ""
    Unk402 = 0
    Unk403 = 0
    tex_array = []
    col_array = []
    Unk404 = 0
    Unk405 = 0
    Mattname = ""
    Unk406 = 0.0
    Unk407 = []  # 60 bytes padding

    def read_mesh_mat(self, f=fopen()):
        pos = ftell(f)
        i = 0
        self.Unk400 = readLong(f)
        self.Unk401 = readLong(f)
        self.Mattype = readString(f)
        fseek(f, pos + 16, seek_set)
        self.Unk402 = readLong(f)
        self.tex_array = [mesh_mat_tex] * 8
        for i in range(0, 8):
            self.tex_array[i] = mesh_mat_tex()
            self.tex_array[i].read_mat_tex(f)

        self.Unk403 = readLong(f)
        self.col_array = [[float] * 4] * 5
        for i in range(0, 5):
            self.col_array[i] = [readFloat(f), readFloat(f), readFloat(f), readFloat(f)]

        self.Unk404 = readLong(f)
        self.Unk405 = readLong(f)

        self.Mattname = readString(f)
        fseek(f, pos + 1136, seek_set)
        self.Unk406 = readFloat(f)
        self.Unk407 = []
        self.Unk407 = [int] * 60
        for i in range(0, 60):
            self.Unk407[i] = readByte(f, unsigned)


class mesh_geo_box:  # 20 Bytes
    boxid = [0, 0, 0, 0, 0, 0, 0, 0]  # 8bytes, id?
    boxpos = [0.0, 0.0, 0.0]

    def read_geo_box(self, f=fopen()):
        i = 0
        for i in range(0, 8): self.boxid[i] = readByte(f, unsigned)
        self.boxpos = [readFloat(f), readFloat(f), readFloat(f)]


class mesh_geo_face_info:  # 92 Bytes
    Unk300 = mesh_geo_box()
    MatNumber1 = 0
    Unk301 = [0, 0, 0, 0, 0, 0, 0, 0]  # 8 bytes Padding?
    FCount1 = 0  # number of bones in bone pallete
    FOffset1 = 0  # address bone pallete
    Num4 = 0
    Ftype = 0
    Num1 = 0
    FCount2 = 0  # number of face indices
    FOffset2 = 0  # address face indices
    Unk302 = []  # 32bytes Padding?

    def read_geo_face_info(self, f=fopen()):
        i = 0
        self.Unk300.read_geo_box(f)
        self.MatNumber1 = readLong(f)
        for i in range(0, 8): self.Unk301[i] = readByte(f, unsigned)
        self.FCount1 = readLong(f)
        self.FOffset1 = readLong(f)
        self.Num4 = readLong(f)
        self.Ftype = readLong(f)
        self.Num1 = readLong(f)
        self.FCount2 = readLong(f)
        self.FOffset2 = readLong(f)
        self.Unk302 = [int] * 64
        for i in range(0, 64): self.Unk302[i] = readByte(f, unsigned)


class cmf_mesh_geo:  # Variable Size
    Unk200 = mesh_geo_box()
    MeshFaceSectionCount = 0
    MeshFaceHeaderOff = 0
    C13_17 = 0  # count?
    Num0x50 = 0  # ?always 0x50
    VertCount = 0
    VertStart = 0
    NormalStart = 0
    VertColorStart = 0
    Null01 = 0
    UvStart = []  # 20bytes, padding?
    WeightStart = 0
    BoneParIDstart = 0
    Unk203 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
              0]  # 64bytes, padding? or maybe a name?
    MeshName = ""
    face_info = []
    vertex_array = []
    normal_array = []
    colour_array = []  # ?? tangents
    texcoord_array = []
    bonepal_array = []
    face_array = []
    weight_array = []
    boneid_array = []

    def read_mesh_geo(self, f=fopen(), BaseOff=0):  # 216 Bytes
        i = 0
        self.Unk200.read_geo_box(f)
        self.MeshFaceSectionCount = readLong(f)
        self.MeshFaceHeaderOff = readLong(f)
        self.C13_17 = readLong(f)
        self.Num0x50 = readLong(f)
        self.VertCount = readLong(f)
        self.VertStart = readLong(f)
        self.NormalStart = readLong(f)
        self.VertColorStart = readLong(f)
        self.Null01 = readLong(f)
        for i in range(0, 6): self.UvStart.append(readLong(f, unsigned))
        self.WeightStart = readLong(f)
        self.BoneParIDstart = readLong(f)
        # FaceStart = self.BoneParIDstart + (0x10 * self.VertCount))
        for i in range(0, 64): self.Unk203[i] = readByte(f, unsigned)
        self.MeshName = readString(f)

        if self.MeshFaceSectionCount > 0:
            self.face_info = [mesh_geo_face_info] * self.MeshFaceSectionCount
            for i in range(0, self.MeshFaceSectionCount):
                fseek(f, BaseOff + self.MeshFaceHeaderOff + (i * 92), seek_set)
                self.face_info[i] = mesh_geo_face_info()
                self.face_info[i].read_geo_face_info(f)

        if self.VertCount > 0:

            fseek(f, BaseOff + self.VertStart, seek_set)
            self.vertex_array = [[float] * 3] * self.VertCount
            for i in range(0, self.VertCount):
                self.vertex_array[i] = (readFloat(f), readFloat(f), readFloat(f))

            fseek(f, BaseOff + self.NormalStart, seek_set)
            self.normal_array = [[float] * 3] * self.VertCount
            for i in range(0, self.VertCount):
                self.normal_array[i] = (readFloat(f), readFloat(f), readFloat(f))

            fseek(f, BaseOff + self.VertColorStart, seek_set)
            self.colour_array = [[float] * 4] * self.VertCount
            for i in range(0, self.VertCount):
                self.colour_array[i] = (readFloat(f), readFloat(f), readFloat(f), readFloat(f))
            
            #self.texcoord_array = [   [[[float] * 2] * self.VertCount]  * 6 ]
            fuck = 0
            for x in (0, len(self.UvStart)):
                #self.texcoord_array[x] = []
                
                #print (fuck)
                if self.UvStart[fuck] > 0:
                    self.texcoord_array.append([])
                    #self.texcoord_array[x] = [[float] * 2] * self.VertCount
                    fseek(f, BaseOff + self.UvStart[fuck], seek_set)
                    for i in range(0, self.VertCount):
                        #self.texcoord_array[x][i] = (readFloat(f), readFloat(f))
                        self.texcoord_array[fuck].append((readFloat(f), readFloat(f)))
                    fuck+=1

            fseek(f, BaseOff + self.WeightStart, seek_set)
            self.weight_array = [[float] * 3] * self.VertCount
            for i in range(0, self.VertCount):
                self.weight_array[i] = (readFloat(f), readFloat(f), readFloat(f), readFloat(f))

            fseek(f, BaseOff + self.BoneParIDstart, seek_set)
            self.boneid_array = [[float] * 4] * self.VertCount
            for i in range(0, self.VertCount):
                self.boneid_array[i] = (readFloat(f), readFloat(f), readFloat(f), readFloat(f))

        if self.MeshFaceSectionCount > 0:
            m = 0
            self.face_array = [int] * self.MeshFaceSectionCount
            self.bonepal_array = [int] * self.MeshFaceSectionCount
            for m in range(0, self.MeshFaceSectionCount):

                # Read Bone Pallete
                fseek(f, self.face_info[m].FOffset1 + BaseOff, seek_set)
                self.bonepal_array[m] = []
                if self.face_info[m].FCount1 > 0:
                    self.bonepal_array[m] = [int] * self.face_info[m].FCount1
                    for i in range(0, self.face_info[m].FCount1):
                        self.bonepal_array[m][i] = readShort(f)

                # Read Face Indices
                fseek(f, (self.face_info[m].FOffset2 + BaseOff), seek_set)
                self.face_array[m] = []
                if self.face_info[m].FCount2 > 0:
                    self.face_array[m] = [int] * self.face_info[m].FCount2
                    for i in range(0, self.face_info[m].FCount2):
                        self.face_array[m][i] = readShort(f)


class cmf_mesh_table:  # 40 Bytes
    Unk100 = 0
    Unk101 = 0
    Unk102 = 0
    Unk103 = 0.0
    Unk104 = 0.0
    Unk105 = 0.0
    Unk106 = 0.0
    MeshCount = 0
    MeshTableStart = 0
    MaterialCount = 0
    MaterialOffset = 0
    mesh_geo = []
    mesh_mat = []

    def read_mesh_table(self, f=fopen()):
        BaseOff = ftell(f)

        i = 0
        self.Unk100 = readShort(f)
        self.Unk101 = readShort(f)
        self.Unk102 = readLong(f)
        self.Unk103 = readFloat(f)
        self.Unk104 = readFloat(f)
        self.Unk105 = readFloat(f)
        self.Unk106 = readFloat(f)
        self.MeshCount = readLong(f)
        self.MeshTableStart = readLong(f)
        self.MaterialCount = readLong(f)
        self.MaterialOffset = readLong(f)

        if self.MeshCount > 0:
            self.mesh_geo = [cmf_mesh_geo] * self.MeshCount
            for i in range(0, self.MeshCount):
                fseek(f, self.MeshTableStart + BaseOff + (i * 216), seek_set)
                self.mesh_geo[i] = cmf_mesh_geo()
                self.mesh_geo[i].read_mesh_geo(f, BaseOff)
                f
                BaseOff

        if self.MaterialCount > 0:
            fseek(f, self.MaterialOffset + BaseOff, seek_set)
            self.mesh_mat = [cmf_mesh_mat] * self.MaterialCount
            for i in range(0, self.MaterialCount):
                self.mesh_mat[i] = cmf_mesh_mat()
                self.mesh_mat[i].read_mesh_mat(f)
            # print(self.mesh_mat[i])


class cmf_file:  # All blocks are padded, a byte alignment of 32bytes
    # Header
    Idstring = 0
    SectionCount = 0
    BoneCount = 0
    SectionTableOff = 0
    BoneTableOff1 = 0
    MeshNameOff = 0
    MeshNameIdOff1 = 0
    MeshNameIdOff2 = 0  # texture id addr
    MeshNameIdOffCount = 0  # texture id count
    Unk10 = 0
    Unk11 = 0
    # Bytes padded 32 here
    SectionAddrs = []
    BoneAddrs = []
    SectionTable = []
    BoneParIDs = []
    BoneParStrs = []
    BoneParStrAddrs = []
    BoneParInfo = []
    texture_ids = []

    def read_cmf(self, f=fopen()):

        self.Idstring = readLong(f, unsigned)

        if self.Idstring == 0x05062500:
            i = 0
            hasBones = False
            # Read Header
            self.SectionCount = readLong(f, unsigned)

            self.BoneCount = readLong(f, unsigned)
            self.SectionTableOff = readLong(f, unsigned)
            self.BoneTableOff1 = readLong(f, unsigned)
            self.MeshNameOff = readLong(f, unsigned)
            self.MeshNameIdOff1 = readLong(f, unsigned)
            self.MeshNameIdOff2 = readLong(f, unsigned)
            self.MeshNameIdOffCount = readLong(f, unsigned)
            Unk10 = readLong(f, unsigned)
            Unk11 = readLong(f, unsigned)

            # Read Section Addresses
            if self.SectionCount > 0 and self.SectionTableOff > 0:

                if self.SectionTableOff > 0:
                    fseek(f, self.SectionTableOff, seek_set)
                    self.SectionAddrs = [int] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        self.SectionAddrs[i] = readLong(f, unsigned)

                if self.BoneTableOff1 > 0:
                    fseek(f, self.BoneTableOff1, seek_set)
                    self.BoneAddrs = [int] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        self.BoneAddrs[i] = readLong(f, unsigned)
                        if not hasBones and self.BoneAddrs[i] > 0:
                            hasBones = True

            if self.SectionCount > 0:
                self.SectionTable = [cmf_mesh_table] * self.SectionCount
                for i in range(0, self.SectionCount):
                    fseek(f, self.SectionAddrs[i], seek_set)
                    self.SectionTable[i] = cmf_mesh_table()
                    self.SectionTable[i].read_mesh_table(f)

                # Read Bone Parent ID's
                fseek(f, self.MeshNameIdOff1, seek_set)
                if self.MeshNameIdOff1 > 0:
                    self.BoneParIDs = [int] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        self.BoneParIDs[i] = readLong(f, unsigned)

                # Read Bone Parent String Offsets
                if self.MeshNameOff > 0:
                    fseek(f, self.MeshNameOff, seek_set)
                    self.BoneParStrAddrs = [int] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        self.BoneParStrAddrs[i] = readLong(f, unsigned)

                    # Read Bone Parent Strings
                    fseek(f, self.MeshNameOff, seek_set)
                    self.BoneParStrs = [str] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        fseek(f, self.BoneParStrAddrs[i], seek_set)
                        self.BoneParStrs[i] = readString(f)

                if len(self.BoneAddrs) > 0:
                    self.BoneParInfo = [cmf_bone_info] * self.SectionCount
                    for i in range(0, self.SectionCount):
                        if self.BoneAddrs[i] > 0:
                            fseek(f, self.BoneAddrs[i], seek_set)
                            self.BoneParInfo[i] = cmf_bone_info()
                            self.BoneParInfo[i].read_bone_info(f)

                if self.MeshNameIdOff2 > 0 and self.MeshNameIdOffCount > 0:
                    fseek(f, self.MeshNameIdOff2, seek_set)
                    self.texture_ids = [int] * self.MeshNameIdOffCount
                    for i in range(0, self.MeshNameIdOffCount):
                        self.texture_ids[i] = readLong(f, unsigned)

                # print (self.texture_ids as string)
                if hasBones:
                    for i in range(0, self.SectionCount):
                        self.BoneParInfo[i].read_bone_buffers(f)
                        # try:
                        #    self.BoneParInfo[i].read_bone_buffers(f)
                        # except:
                        #    pass
                        # else:
                        #    hasBones = False
                        #    self.BoneCount = 0
                        #    self.SectionCount = 0
                        #    print("Bone Error?\t%s\n" % (f.file))






        else:
            messageBox("Failed, open File.\n")


class dds_header:
    isDX10 = False
    dwMagic = 0x20534444
    dwSize = 0x7C
    dwFlags = 0x0002100F
    dwHeight = 0
    dwWidth = 0
    dwPitch = 0
    dwLinearSize = 0
    dwDepth = 0
    dwMipMapCount = 0,
    dwReserved1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    fmSize = 0x20
    fmFlags = 0x04
    fmFourCC = 0x30315844
    dxgiFormat = 0
    resourceDimension = 0
    miscFlag = 0
    arraySize = 0
    miscFlags2 = 0
    dwRGBBitCount = 0x00401008
    dwRBitMask = 0
    dwGBitMask = 0
    dwBBitMask = 0
    dwABitMask = 0
    dwCaps = 0x00401008
    dwCaps2 = 3
    dwCaps3 = 0
    dwCaps4 = 1
    dwReserved2 = 0

    def write_dds_header(self, s=fopen(), width=8, height=8, type='None', mips=1):
        self.dwWidth = width
        self.dwHeight = height
        self.dwMipMapCount = mips
        if type == 'DXT1':
            self.fmFourCC = 0x31545844
            self.dwFlags = 0x000A1007
            self.dwPitch = self.dwWidth * self.dwHeight / 2
            self.dwLinearSize = (self.dwWidth + 3) / 4
            if self.dwLinearSize < 1: self.dwLinearSize = 1
            self.dwLinearSize *= 4
            self.dwRGBBitCount = 0

        elif type == 'DXT3':
            self.fmFourCC = 0x33545844
            self.dwFlags = 0x000A1007
            self.dwPitch = self.dwWidth * self.dwHeight
            self.dwLinearSize = (self.dwWidth + 3) / 4
            if self.dwLinearSize < 1: self.dwLinearSize = 1
            self.dwLinearSize *= 8
            self.dwRGBBitCount = 0

        elif type == 'DXT5':
            self.fmFourCC = 0x35545844
            self.dwFlags = 0x000A1007
            self.dwPitch = self.dwWidth * self.dwHeight
            self.dwLinearSize = (self.dwWidth + 3) / 4
            if self.dwLinearSize < 1: self.dwLinearSize = 1
            self.dwLinearSize *= 8
            self.dwRGBBitCount = 0

        elif type == 'ATN2':
            self.fmFourCC = 0x32495441
            self.dwFlags = 0x000A1007
            self.dwPitch = self.dwWidth * self.dwHeight
            self.dwLinearSize = (self.dwWidth + 3) / 4
            if self.dwLinearSize < 1: self.dwLinearSize = 1
            self.dwLinearSize *= 8
            self.dwRGBBitCount = 0

        elif type == 'RGBA16':
            self.dwPitch = self.dwWidth * self.dwHeight * 2

        elif type == 'RGBA32':
            self.fmFourCC = 0x00000000
            self.fmFlags = 0x00000041
            self.dwPitch = self.dwWidth * self.dwHeight * 4
            self.dwLinearSize = (self.dwWidth * 32 + 7) / 8
            self.dwRGBBitCount = 0x20

        writeLong(s, self.dwMagic)
        writeLong(s, self.dwSize)
        writeLong(s, self.dwFlags)
        writeLong(s, self.dwHeight)
        writeLong(s, self.dwWidth)
        writeLong(s, self.dwPitch)
        writeLong(s, self.dwDepth)
        writeLong(s, self.dwMipMapCount)
        writeLong(s, self.dwReserved1[0])
        writeLong(s, self.dwReserved1[1])
        writeLong(s, self.dwReserved1[2])
        writeLong(s, self.dwReserved1[3])
        writeLong(s, self.dwReserved1[4])
        writeLong(s, self.dwReserved1[5])
        writeLong(s, self.dwReserved1[6])
        writeLong(s, self.dwReserved1[7])
        writeLong(s, self.dwReserved1[8])
        writeLong(s, self.dwReserved1[9])
        writeLong(s, self.dwReserved1[10])
        writeLong(s, self.fmSize)
        writeLong(s, self.fmFlags)
        writeLong(s, self.fmFourCC)
        if self.isDX10:
            writeLong(s, self.dxgiFormat)
            writeLong(s, self.resourceDimension)
            writeLong(s, self.miscFlag)
            writeLong(s, self.arraySize)
            writeLong(s, self.miscFlags2)

        writeLong(s, self.dwRGBBitCount)
        writeLong(s, self.dwRBitMask)
        writeLong(s, self.dwGBitMask)
        writeLong(s, self.dwBBitMask)
        writeLong(s, self.dwABitMask)
        writeLong(s, self.dwCaps)
        writeLong(s, self.dwCaps2)
        writeLong(s, self.dwCaps3)
        writeLong(s, self.dwCaps4)
        writeLong(s, self.dwReserved2)


def read_txp_data(f=fopen(), prefix="tex_", fsize=0, num2=1, num3=1, num4=1):
    pos = ftell(f)
    count = 0
    tex_count = 0
    unk2_count = 0
    unk3_count = 0
    unk4_count = 0
    addrs = []
    width = 0
    height = 0
    type = 0  # 6=DXT1, 7=DXT3, 9=DXT5, 11=ATN2
    unk5 = 0
    size = 0
    n1 = ""
    n2 = ""
    n3 = ""

    fileid = 0
    try:
        fileid = readLong(f, unsigned)
    except:
        pass

    if fileid == 0x03505854:  # TXP, Type 3 = Image Pack
        num3 += 1
        count = readLong(f, unsigned)
        tex_count = readByte(f, unsigned)
        unk2_count = readByte(f, unsigned)
        unk3_count = readByte(f, unsigned)
        unk4_count = readByte(f, unsigned)

        if count > 0:
            addrs = [int] * count
            for i in range(0, count):
                addrs[i] = readLong(f, unsigned)

            for i in range(0, count):
                if addrs[i] < fsize:
                    fseek(f, pos + addrs[i], seek_set)
                    num2, num3, num4 = read_txp_data(f, prefix, fsize, num2, num3, num4)




    elif fileid == 0x04505854:  # TXP, Type 4 = Image Container
        num4 += 1
        count = readLong(f, unsigned)
        tex_count = readByte(f, unsigned)
        unk2_count = readByte(f, unsigned)
        unk3_count = readByte(f, unsigned)
        unk4_count = readByte(f, unsigned)
        if count > 0:
            addrs = [int] * count
            for i in range(0, count):
                addrs[i] = readLong(f, unsigned)

            count = 1
            for i in range(0, count):
                if addrs[i] < fsize:
                    fseek(f, pos + addrs[i], seek_set)
                    num2, num3, num4 = read_txp_data(f, prefix, fsize, num2, num3, num4)




    elif fileid == 0x05505854:  # TXP, Type 5 = CubeMap
        num4 += 1
        count = readLong(f, unsigned)
        tex_count = readByte(f, unsigned)
        unk2_count = readByte(f, unsigned)
        unk3_count = readByte(f, unsigned)
        unk4_count = readByte(f, unsigned)
        if count > 0:
            addrs = [int] * count
            for i in range(0, count):
                addrs[i] = readLong(f, unsigned)

            count = 1
            for i in range(0, count):
                if addrs[i] < fsize:
                    fseek(f, pos + addrs[i], seek_set)
                    num2, num3, num4 = read_txp_data(f, prefix, fsize, num2, num3, num4)




    elif fileid == 0x02505854:  # TXP, Type 2 = Image Data
        num2 += 1
        width = readLong(f, unsigned)
        height = readLong(f, unsigned)
        type = readLong(f, unsigned)
        unk5 = readLong(f, unsigned)
        size = readLong(f, unsigned)
        if size > 0:
            fname = getFilenameFile(f.file)
            fpath = getFilenamePath(f.file)
            d = dds_header()

            # make a path
            makeDir(fpath + fname)

            # texName = '{:04d}'.format(int(''.join([str(s) for s in fname if s.isdigit()]))) # pads string to 4 places
            # texName = ''.join([str(s) for s in fname if s.isdigit()])  # does not pad string at all

            s = fopen(fpath + fname + "\\" + prefix + '{:04d}'.format(num4 - 1) + ".dds", "wb")
            s.resize(128 + size)
            print("Img %i\t%i\t%i" % (num4, width, height))
            if type == 6:
                d.write_dds_header(s, width, height, 'DXT1')
            elif type == 7:
                d.write_dds_header(s, width, height, 'DXT3')
            elif type == 9:
                d.write_dds_header(s, width, height, 'DXT5')
            elif type == 11:
                d.write_dds_header(s, width, height, 'ATN2')
            elif type == 204:
                d.write_dds_header(s, width, height, 'DXT1')
            else:
                print("Error:\tUnsupported Type:\t[%i]" % (type))

            for i in range(0, size):
                writeByte(s, readByte(f, unsigned))

            s.flush()
    return num2, num3, num4


def read_txp(file, prefix="tex_"):
    n2 = 0
    n3 = 0
    n4 = 0
    f = fopen(file, 'rb')

    if f.isGood:
        read_txp_data(f, prefix, f.size, n2, n3, n4)
    else:
        print("Error:\t%s" % (file))


def extractNum(name_nums, bone_name):  # Needed for the guessParents algo
    nums = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    n = ""
    for i in range(0, len(name_nums)):
        if not name_nums[i]:
            if findItem(nums, bone_name[i]) > -1:
                n += bone_name[i]
            else:
                n += str(i)
    return int(n)


def parent_from_bonenames(boneArray, root_names):
    # Find Chains of Bones using the patterns in the VF5 bone Names

    boneNameLookUp = []
    boneChains = []
    bname_alpha = ""
    bname_index = 0
    iii = 1
    nums = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "r", "l", "f", "b"]
    # Inspect the Name of each Bone
    for o in boneArray.armature.data.edit_bones:

        # If Name is not a 'protected' bone then get name of bone
        if findItem(root_names, o.name) == -1:

            # Get Name of Bone and filter out any characters from nums array
            bname_alpha = ""
            for iii in range(0, len(o.name)):
                if findItem(nums, o.name[iii]) == -1:
                    bname_alpha += o.name[iii]

            # Assign Bones to a array group
            bname_index = findItem(boneNameLookUp, bname_alpha)
            if bname_index == -1:
                bname_index = len(boneNameLookUp)
                append(boneNameLookUp, bname_alpha)

            if len(boneChains) < bname_index + 1:
                boneChains.append([])
            # print("bname_index:\t%i" % bname_index)
            boneChains[bname_index].append(o.name)

    # Try to parent across discovered chains
    if len(boneChains) > 0:

        # Get Chain Groups
        isNameLenSame = False
        strLen = 0
        c = []
        name_nums = []
        ii = 1

        # Example Each Bone Chain
        for c in boneChains:

            # Exit if there is no bone chain
            if len(c) <= 1: continue  # skip

            # Check if there is a name pattern that can be exploited
            isNameLenSame = True
            strLen = len(c[0])
            for i in range(0, len(c)):
                if len(c[i]) != strLen:
                    isNameLenSame = False
                    break

            # Exit if there is no pattern
            if not isNameLenSame: continue  # skip

            # Sort String Backwards
            c.sort(reverse=True)

            # Identify which character's in the bones name changes
            name_nums = [True] * strLen
            # name_nums = list(range(0, strLen))
            for i in range(0, len(c)):
                for ii in range(0, strLen):
                    name_nums[ii] = True
                    if c[0][ii] != c[i][ii]:
                        name_nums[ii] = False

            # if the numberical value in the name is is decending order, then parent them
            for i in range(0, len(c) - 1):
                if (extractNum(name_nums, c[i]) - 1) == (extractNum(name_nums, c[i + 1])):
                    # Parent Bone
                    boneArray.getNodeByName(c[i]).parent = boneArray.getNodeByName(c[i + 1])

    # Check if protected bones are present
    protectedBones = []
    for s in root_names:
        b = boneArray.getNodeByName(s)
        if b != None:
            append(protectedBones, b)

    # If protected bones are present then parent anything not parented to them
    if len(protectedBones) > 0:
        dis = []
        tmp = []
        index = 0
        for b in boneArray.armature.data.edit_bones:
            if b.parent == None and findItem(protectedBones, b) == -1:
                dis = []
                tmp = []
                tmp = [float] * len(protectedBones)
                dis = [float] * len(protectedBones)
                for i in range(0, len(protectedBones)):
                    tmp[i] = distance(b.head, protectedBones[i].head)
                    dis[i] = tmp[i]
                tmp.sort()
                b.parent = protectedBones[findItem(dis, tmp[1])]

    return None


def read(file, impBones=False, armName="Armature", impNormals=False, impColours=False, impWeights=False,
         guessParents=False,
         unpack_tex=True, mscale=1.0):
    f = fopen(file, 'rb')
    if f.isGood:

        # Read File into CMF Class
        cmf = cmf_file()
        cmf.read_cmf(f)

        # Collect Filepath Parts
        fpath = getFilenamePath(file)
        fname = getFilenameFile(file)

        if "_obj" in fname:
            fname = fname[0:(fname.find("_obj"))]

        texPath = fpath + fname + "_tex\\"
        texName = ""

        # prefix = '{:04d}'.format(int(''.join([str(s) for s in fname if s.isdigit()]))) # pads string to 4 places
        # print("fname:\t%s" % (fname))
        prefix = ''.join([str(s) for s in fname if s.isdigit()])  # does not pad string at all
        # print("prefix:\t%s" % (prefix))

        if unpack_tex:
            read_txp(fpath + fname + "_tex.bin", prefix)

        # Build Skeleton
        boneArray = None
        usedBoneIds = []
        usedBoneNames = []
        children = []
        childPos = (0.0, 0.0, 0.0)
        parPos = (0.0, 0.0, 0.0)
        childPosAvg = [0.0, 0.0, 0.0]
        boneLength = 0.0
        boneNorm = (0.0, 0.0, 0.0)
        if impBones:
            # Create Armature
            boneArray = boneSys(armName)
            # print("SectionCount:\t%i" % cmf.SectionCount)
            for i in range(0, cmf.SectionCount):

                # print("BoneCount:\t%i" % cmf.BoneParInfo[i].BoneCount)
                for ii in range(0, cmf.BoneParInfo[i].BoneCount):

                    boneID_index = findItem(usedBoneIds, cmf.BoneParInfo[i].childIds[ii])
                    # print("boneID_index:\t%i" % boneID_index)
                    if boneID_index == -1:
                        append(usedBoneIds, cmf.BoneParInfo[i].childIds[ii])
                        append(usedBoneNames, cmf.BoneParInfo[i].childStrings[ii])
                        t = cmf.BoneParInfo[i].childMatrices[ii].inverse()

                        # Create Bone
                        boneArray.createBone(
                            cmf.BoneParInfo[i].childStrings[ii],
                            (t.row4[0] * mscale, -t.row4[2] * mscale, t.row4[1] * mscale),
                            ((t.row4[0] + 0.1) * mscale, -t.row4[2] * mscale, t.row4[1] * mscale)
                        )

                        # Modify Bone
                        boneArray.editMode(True)
                        # boneArray.setTransform(cmf.BoneParInfo[i].childStrings[ii], t.asMat4())
                        boneArray.setUserProp(cmf.BoneParInfo[i].childStrings[ii], "id",
                                              cmf.BoneParInfo[i].childIds[ii])
                        boneArray.editMode(False)

            # Set Parents
            
            if guessParents:

                # Enter Edit Mode
                boneArray.editMode(True)
                # Root Bone Names
                root_names = [
                    "kl_kosi_etc_wj",
                    "j_momo_l_wj",
                    "j_sune_l_wj",
                    "kl_asi_l_wj_co",
                    "j_momo_r_wj",
                    "j_sune_r_wj",
                    "kl_asi_r_wj_co",
                    "kl_mune_b_wj",
                    "kl_waki_l_wj",
                    "j_kata_l_wj_cu",
                    "j_ude_l_wj",
                    "kl_te_l_wj",
                    "kl_waki_r_wj",
                    "j_kata_r_wj_cu",
                    "j_ude_r_wj",
                    "kl_te_r_wj",
                    "n_kubi_wj_ex",
                    "j_kao_wj"
                ]

                # Parent List
                boneArray.setParent('n_hara_b_wj_ex', 'kl_kosi_etc_wj')
                boneArray.setParent('j_momo_l_wj', 'kl_kosi_etc_wj')
                boneArray.setParent('j_sune_l_wj', 'j_momo_l_wj')
                boneArray.setParent('kl_asi_l_wj_co', 'j_sune_l_wj')
                boneArray.setParent('kl_toe_l_wj', 'kl_asi_l_wj_co')
                boneArray.setParent('n_hiza_l_wj_ex', 'j_sune_l_wj')
                boneArray.setParent('n_momo_b_l_wj_ex', 'j_momo_l_wj')
                boneArray.setParent('n_momo_c_l_wj_ex', 'j_momo_l_wj')
                boneArray.setParent('j_momo_r_wj', 'kl_kosi_etc_wj')
                boneArray.setParent('j_sune_r_wj', 'j_momo_r_wj')
                boneArray.setParent('kl_asi_r_wj_co', 'j_sune_r_wj')
                boneArray.setParent('kl_toe_r_wj', 'kl_asi_r_wj_co')
                boneArray.setParent('n_hiza_r_wj_ex', 'j_sune_r_wj')
                boneArray.setParent('n_momo_b_r_wj_ex', 'j_momo_r_wj')
                boneArray.setParent('n_momo_c_r_wj_ex', 'j_momo_r_wj')
                boneArray.setParent('n_ketu_l_wj_ex', 'kl_kosi_etc_wj')
                boneArray.setParent('j_ketu_l_000wj', 'kl_kosi_etc_wj')
                boneArray.setParent('n_ketu_r_wj_ex', 'kl_kosi_etc_wj')
                boneArray.setParent('j_ketu_r_000wj', 'kl_kosi_etc_wj')
                boneArray.setParent('j_hara_wj', 'kl_kosi_etc_wj')
                boneArray.setParent('j_mune_wj', 'kl_kosi_etc_wj')
                boneArray.setParent('kl_mune_b_wj', 'j_mune_wj')
                boneArray.setParent('kl_waki_l_wj', 'kl_mune_b_wj')
                boneArray.setParent('j_kata_l_wj_cu', 'kl_waki_l_wj')
                boneArray.setParent('n_skata_b_l_wj_cd_cu_ex', 'j_kata_l_wj_cu')
                boneArray.setParent('n_skata_c_l_wj_cd_cu_ex', 'j_kata_l_wj_cu')
                boneArray.setParent('n_skata_l_wj_cd_ex', 'j_kata_l_wj_cu')
                boneArray.setParent('j_ude_l_wj', 'j_kata_l_wj_cu')
                boneArray.setParent('kl_te_l_wj', 'j_ude_l_wj')
                boneArray.setParent('nl_hito_l_wj', 'kl_te_l_wj')
                boneArray.setParent('nl_hito_b_l_wj', 'nl_hito_l_wj')
                boneArray.setParent('nl_hito_c_l_wj', 'nl_hito_b_l_wj')
                boneArray.setParent('nl_ko_l_wj', 'kl_te_l_wj')
                boneArray.setParent('nl_ko_b_l_wj', 'nl_ko_l_wj')
                boneArray.setParent('nl_ko_c_l_wj', 'nl_ko_b_l_wj')
                boneArray.setParent('nl_kusu_l_wj', 'kl_te_l_wj')
                boneArray.setParent('nl_kusu_b_l_wj', 'nl_kusu_l_wj')
                boneArray.setParent('nl_kusu_c_l_wj', 'nl_kusu_b_l_wj')
                boneArray.setParent('nl_naka_l_wj', 'kl_te_l_wj')
                boneArray.setParent('nl_naka_b_l_wj', 'nl_naka_l_wj')
                boneArray.setParent('nl_naka_c_l_wj', 'nl_naka_b_l_wj')
                boneArray.setParent('nl_oya_l_wj', 'kl_te_l_wj')
                boneArray.setParent('nl_oya_b_l_wj', 'nl_oya_l_wj')
                boneArray.setParent('nl_oya_c_l_wj', 'nl_oya_b_l_wj')
                boneArray.setParent('n_ste_l_wj_ex', 'j_ude_l_wj')
                boneArray.setParent('n_sude_b_l_wj_ex', 'j_ude_l_wj')
                boneArray.setParent('n_sude_l_wj_ex', 'j_ude_l_wj')
                boneArray.setParent('n_hiji_l_wj_ex', 'j_kata_l_wj_cu')
                boneArray.setParent('n_tekug_l_ex_wj', 'n_hiji_l_wj_ex')
                boneArray.setParent('n_tekuc_l_ex_wj', 'n_tekug_l_ex_wj')
                boneArray.setParent('n_tekub_l_ex_wj', 'n_tekuc_l_ex_wj')
                boneArray.setParent('kl_waki_r_wj', 'kl_mune_b_wj')
                boneArray.setParent('j_kata_r_wj_cu', 'kl_waki_r_wj')
                boneArray.setParent('n_skata_b_r_wj_cd_cu_ex', 'j_kata_r_wj_cu')
                boneArray.setParent('n_skata_c_r_wj_cd_cu_ex', 'j_kata_r_wj_cu')
                boneArray.setParent('n_skata_r_wj_cd_ex', 'j_kata_r_wj_cu')
                boneArray.setParent('j_ude_r_wj', 'j_kata_r_wj_cu')
                boneArray.setParent('kl_te_r_wj', 'j_ude_r_wj')
                boneArray.setParent('nl_hito_r_wj', 'kl_te_r_wj')
                boneArray.setParent('nl_hito_b_r_wj', 'nl_hito_r_wj')
                boneArray.setParent('nl_hito_c_r_wj', 'nl_hito_b_r_wj')
                boneArray.setParent('nl_ko_r_wj', 'kl_te_r_wj')
                boneArray.setParent('nl_ko_b_r_wj', 'nl_ko_r_wj')
                boneArray.setParent('nl_ko_c_r_wj', 'nl_ko_b_r_wj')
                boneArray.setParent('nl_kusu_r_wj', 'kl_te_r_wj')
                boneArray.setParent('nl_kusu_b_r_wj', 'nl_kusu_r_wj')
                boneArray.setParent('nl_kusu_c_r_wj', 'nl_kusu_b_r_wj')
                boneArray.setParent('nl_naka_r_wj', 'kl_te_r_wj')
                boneArray.setParent('nl_naka_b_r_wj', 'nl_naka_r_wj')
                boneArray.setParent('nl_naka_c_r_wj', 'nl_naka_b_r_wj')
                boneArray.setParent('nl_oya_r_wj', 'kl_te_r_wj')
                boneArray.setParent('nl_oya_b_r_wj', 'nl_oya_r_wj')
                boneArray.setParent('nl_oya_c_r_wj', 'nl_oya_b_r_wj')
                boneArray.setParent('n_ste_r_wj_ex', 'j_ude_r_wj')
                boneArray.setParent('n_sude_b_r_wj_ex', 'j_ude_r_wj')
                boneArray.setParent('n_sude_r_wj_ex', 'j_ude_r_wj')
                boneArray.setParent('n_hiji_r_wj_ex', 'j_kata_r_wj_cu')
                boneArray.setParent('n_kubi_wj_ex', 'kl_mune_b_wj')
                boneArray.setParent('j_kao_wj', 'n_kubi_wj_ex')
                boneArray.setParent('kl_eye_l_wj', 'j_kao_wj')
                boneArray.setParent('kl_eye_r_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_d_l_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_d_r_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_l_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_r_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_u_l_wj', 'j_kao_wj')
                boneArray.setParent('kl_mabu_u_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_ha_wj', 'j_kao_wj')
                boneArray.setParent('kl_ago_wj', 'tl_ha_wj')
                boneArray.setParent('tl_ago_wj', 'kl_ago_wj')
                boneArray.setParent('tl_kuti_d_l_wj', 'kl_ago_wj')
                boneArray.setParent('tl_kuti_d_r_wj', 'kl_ago_wj')
                boneArray.setParent('tl_kuti_d_wj', 'kl_ago_wj')
                boneArray.setParent('tl_hoho_b_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_hoho_b_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_hoho_c_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_hoho_c_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_hoho_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_hoho_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_kuti_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_kuti_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_kuti_u_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_kuti_u_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_kuti_u_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_b_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_b_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_c_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_c_r_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_l_wj', 'j_kao_wj')
                boneArray.setParent('tl_mayu_r_wj', 'j_kao_wj')
                boneArray.setParent('itm_ofs_wj', 'n_kubi_wj_ex')
                boneArray.setParent('j_1_nckls_000wj', 'itm_ofs_wj')
                boneArray.setParent('j_1_nckls_001wj', 'j_1_nckls_000wj')
                boneArray.setParent('j_1_nckls_002wj', 'j_1_nckls_001wj')
                boneArray.setParent('j_opal_050wj', 'kl_mune_b_wj')
                boneArray.setParent('j_opar_051wj', 'kl_mune_b_wj')
                boneArray.setParent('j_opal_015wj', 'kl_mune_b_wj')
                boneArray.setParent('j_opar_014wj', 'kl_mune_b_wj')
                boneArray.setParent('j_opal_058wj', 'kl_mune_b_wj')
                boneArray.setParent('j_0_munl_000wj', 'kl_mune_b_wj')
                boneArray.setParent('n_hara_l_wj_ex', 'kl_mune_b_wj')
                boneArray.setParent('n_hara_r_wj_ex', 'kl_mune_b_wj')
                boneArray.setParent('j_0_munr_000wj', 'kl_mune_b_wj')
                boneArray.setParent('j_opar_059wj', 'kl_mune_b_wj')
                boneArray.setParent('n_hara_c_wj_ex', 'j_mune_wj')
                boneArray.setParent('n_kaha_xz_wj_ex', 'kl_kosi_etc_wj')
                boneArray.setParent('n_joha_xz_wj_ex', 'kl_kosi_etc_wj')

                parent_from_bonenames(boneArray, root_names)

                # Rebuild Bone Directions (this destroys their original rotations!! yay)
                for b in boneArray.armature.data.edit_bones:
                    children = boneArray.getChildren(b.name)
                    if len(children) == 1:  # Only One Child, Link End to the Child
                        boneArray.setEndPosition(b.name, boneArray.getPosition(children[0].name))
                    elif len(children) > 1:  # Multiple Children, Link End to the Average Position of all Children
                        childPosAvg = [0.0, 0.0, 0.0]
                        for c in children:
                            childPos = boneArray.getPosition(c.name)
                            childPosAvg[0] += childPos[0]
                            childPosAvg[1] += childPos[1]
                            childPosAvg[2] += childPos[2]
                        boneArray.setEndPosition(b.name,
                            (childPosAvg[0] / len(children),
                            childPosAvg[1] / len(children),
                            childPosAvg[2] / len(children))
                            )
                    elif b.parent != None:  # No Children use inverse of parent position
                        childPos = boneArray.getPosition(b.name)
                        parPos = boneArray.getPosition(b.parent.name)
                        
                        boneLength = distance(parPos, childPos)
                        boneLength = 0.04 * mscale
                        boneNorm = normalize(
                            (childPos[0] - parPos[0],
                             childPos[1] - parPos[1],
                             childPos[2] - parPos[2])
                            )
                        
                        boneArray.setEndPosition(b.name,
                             (childPos[0] + boneLength * boneNorm[0],
                              childPos[1] + boneLength * boneNorm[1],
                              childPos[2] + boneLength * boneNorm[2])
                             )


                # Exit Edit Mode
                boneArray.editMode(False)

        # Import Mesh
        for i in range(0, cmf.SectionCount):  # Skin Group?   cmf.SectionCount

            # Build Material
            mats = []
            mat = None

            # read each sub material
            for ii in range(0, cmf.SectionTable[i].MaterialCount):

                # make material
                mat = bpy.data.materials.new(
                    name='Material_' + cmf.SectionTable[i].mesh_mat[ii].Mattname + "_" + str(ii))
                mat.use_nodes = True
                mat.use_backface_culling = True
                bsdf = mat.node_tree.nodes["Principled BSDF"]
                bsdf.label = cmf.SectionTable[i].mesh_mat[ii].Mattype
                mixShdr = None
                opaShdr = None

                # Store Colours From Game Material
                for iii in range(0, len(cmf.SectionTable[i].mesh_mat[ii].col_array)):
                    rgbaColor = mat.node_tree.nodes.new('ShaderNodeRGB')
                    rgbaColor.location = (-1350, 575 - (iii * 250))
                    rgbaColor.label = 'Color_' + str(iii + 1)
                    rgbaColor.outputs[0].default_value = (
                        cmf.SectionTable[i].mesh_mat[ii].col_array[iii][0],
                        cmf.SectionTable[i].mesh_mat[ii].col_array[iii][1],
                        cmf.SectionTable[i].mesh_mat[ii].col_array[iii][2],
                        cmf.SectionTable[i].mesh_mat[ii].col_array[iii][3]
                        )
                        


                # Store Textures From Game Material
                # print(len(cmf.SectionTable[i].mesh_mat[ii].tex_array))
                for iii in range(0, len(cmf.SectionTable[i].mesh_mat[ii].tex_array)):

                    if cmf.SectionTable[i].mesh_mat[ii].tex_array[iii].Unk504 > -1:
                        imageTex = mat.node_tree.nodes.new('ShaderNodeTexImage')
                        imageTex.location = (-1100, 695 - (iii * 250))
                        imageTex.label = 'Tex_' + str(iii + 1)

                        if findItem(cmf.texture_ids, cmf.SectionTable[i].mesh_mat[ii].tex_array[iii].Unk504) > -1:
                            texName = '{:04d}'.format(
                                findItem(cmf.texture_ids, cmf.SectionTable[i].mesh_mat[ii].tex_array[iii].Unk504))
                            texName += ".dds"
                            # print (texName)
                            try:
                                imageTex.image = bpy.data.images.load(
                                    filepath=texPath + prefix + texName,
                                    check_existing=False
                                )
                                imageTex.image.name = texName
                                # imageTex.image.file_format = 'TARGA'
                                imageTex.image.colorspace_settings.name = 'sRGB'
                            except:
                                imageTex.image = bpy.data.images.new(
                                    name=prefix + texName,
                                    width=8,
                                    height=8,
                                    alpha=False,
                                    float_buffer=False
                                )
                                imageTex.image.source = 'FILE'
                                imageTex.image.filepath = texName
                                imageTex.image.colorspace_settings.name = 'sRGB'


                        else:
                            print("Image ID Not Found?!\t%i" % (cmf.SectionTable[i].mesh_mat[ii].tex_array[iii].Unk504))

                        # Link Textures to Bidirectional Scattering Distribution Function (BSDF)
                        if iii == 0:  # Diffuse
                            # imageTex = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            # imageTex.location = (-375.666, 272.62)
                            imageTex.label = 'Diffuse'
                            mat.node_tree.links.new(bsdf.inputs['Base Color'], imageTex.outputs['Color'])
                            
                            if cmf.SectionTable[i].mesh_mat[ii].Mattype == 'HAIR':
                                mat.blend_method = 'BLEND'
                                mat.shadow_method = 'HASHED'
                                mat.show_transparent_back = False
                                texName = imageTex.image.filepath
                                imageTex = mat.node_tree.nodes.new('ShaderNodeTexImage')
                                imageTex.location = (-1100, 695 + (1 * 250))
                                imageTex.label = "Opacity"
                                try:
                                    imageTex.image = bpy.data.images.load(
                                        filepath=texName,
                                        check_existing=False
                                        )
                                    imageTex.image.name = texName
                                    # imageTex.image.file_format = 'TARGA'
                                    imageTex.image.colorspace_settings.name = 'Linear'
                                except:
                                    imageTex.image = bpy.data.images.new(
                                        name=texName,
                                        width=8,
                                        height=8,
                                        alpha=False,
                                        float_buffer=False
                                        )
                                    imageTex.image.source = 'FILE'
                                    imageTex.image.filepath = texName
                                    imageTex.image.colorspace_settings.name = 'Linear'


                                if mixShdr == None:
                                    mixShdr = mat.node_tree.nodes.new('ShaderNodeMixShader')
                                    mixShdr.label = 'ShaderNodeMixShader'
                                    mixShdr.location = (253.28, 697.455)

                                if opaShdr == None:
                                    opaShdr = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
                                    opaShdr.label = 'ShaderNodeBsdfTransparent'
                                    opaShdr.location = (86.2229, 483.545)

                                mat.node_tree.links.new(mixShdr.inputs['Fac'], imageTex.outputs['Alpha'])
                                mat.node_tree.links.new(bsdf.inputs['Alpha'], imageTex.outputs['Alpha'])
                                mat.node_tree.links.new(mixShdr.inputs[1], opaShdr.outputs['BSDF'])
                                mat.node_tree.links.new(mixShdr.inputs[2], bsdf.outputs['BSDF'])
                                mat.node_tree.links.new(mat.node_tree.nodes['Material Output'].inputs['Surface'],
                                                        mixShdr.outputs['Shader'])




                        elif iii == 2:  # Normal Map (re-arrange RGB)
                            # imageTex = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            # imageTex.location = (-1112.74, -421.698)
                            imageTex.label = 'Normal'
                            imageTex.image.colorspace_settings.name = 'Linear'
                            
                            splitRGB = mat.node_tree.nodes.new('ShaderNodeSeparateRGB')
                            splitRGB.label = 'ShaderNodeSeparateRGB'
                            splitRGB.location = (-677.741, -318.702)

                            combRGB = mat.node_tree.nodes.new('ShaderNodeCombineRGB')
                            combRGB.label = 'ShaderNodeCombineRGB'
                            combRGB.location = (-450.533, -390.605)
                            combRGB.inputs['B'].default_value = 1

                            normMap = mat.node_tree.nodes.new('ShaderNodeNormalMap')
                            normMap.label = 'ShaderNodeNormalMap'
                            normMap.location = (-230.96, -264.376)

                            mat.node_tree.links.new(splitRGB.inputs['Image'], imageTex.outputs['Color'])
                            mat.node_tree.links.new(combRGB.inputs['G'], imageTex.outputs['Alpha'])
                            mat.node_tree.links.new(combRGB.inputs['R'], splitRGB.outputs['G'])
                            mat.node_tree.links.new(normMap.inputs['Color'], combRGB.outputs['Image'])
                            mat.node_tree.links.new(bsdf.inputs['Normal'], normMap.outputs['Normal'])

                        elif iii == 3:  # Specular Map
                            # imageTex = mat.node_tree.nodes.new('ShaderNodeTexImage')
                            # imageTex.location = (-576.669, -75.4022)
                            imageTex.label = 'Specular'

                            invertRGB = mat.node_tree.nodes.new('ShaderNodeInvert')
                            invertRGB.label = 'ShaderNodeInvert'
                            invertRGB.location = (-220.362, -42.6805)

                            mat.node_tree.links.new(invertRGB.inputs['Color'], imageTex.outputs['Color'])
                            mat.node_tree.links.new(bsdf.inputs['Roughness'], invertRGB.outputs['Color'])

                        # elif iii == 4: # alpha

                        # mat.blend_method = 'BLEND'
                        # mat.shadow_method = 'HASHED'
                        # mat.use_backface_culling = True
                        # mat.show_transparent_back = False

                        # if mixShdr != None:
                        # mixShdr = mat.node_tree.nodes.new('ShaderNodeMixShader')
                        # mixShdr.label = 'ShaderNodeMixShader'
                        # mixShdr.location = (253.28, 697.455)

                        # if opaShdr != None:
                        # opaShdr = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
                        # opaShdr.label = 'ShaderNodeBsdfTransparent'
                        # opaShdr.location = (86.2229, 483.545)

                        # mat.node_tree.links.new(mixShdr.inputs['Fac'], imageTex.outputs['Alpha'])
                        # mat.node_tree.links.new(mixShdr.inputs[1], opaShdr.outputs['BSDF'])
                        # mat.node_tree.links.new(mixShdr.inputs[2], bsdf.outputs['BSDF'])
                        # mat.node_tree.links.new(mat.node_tree.nodes['Material Output'].inputs['Surface'], mixShdr.outputs['Shader'])

                # print(cmf.SectionTable[i].mesh_mat[ii].Mattype)
                if cmf.SectionTable[i].mesh_mat[ii].Mattype == 'SKIN':
                    bsdf.inputs['Subsurface Color'].default_value = (0.8, 0.231883, 0.206407, 1)
                    bsdf.inputs['Subsurface'].default_value = 0.105455
                    
                elif cmf.SectionTable[i].mesh_mat[ii].Mattype == 'EYELENS':
                    glasShdr = mat.node_tree.nodes.new('ShaderNodeBsdfGlass')
                    glasShdr.label = 'ShaderNodeBsdfGlass'
                    # glasShdr.location = (86.2229, 483.545)
                    glasShdr.inputs['Roughness'].default_value = 0.025
                    glasShdr.inputs['IOR'].default_value = 0.400

                    opaShdr = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
                    opaShdr.label = 'ShaderNodeBsdfTransparent'
                    # opaShdr.location = (86.2229, 483.545)

                    mixShdr = mat.node_tree.nodes.new('ShaderNodeMixShader')
                    mixShdr.label = 'ShaderNodeMixShader'
                    # mixShdr.location = (253.28, 697.455)
                    mixShdr.inputs['Fac'].default_value = 0.060

                    mat.node_tree.links.new(mixShdr.inputs[1], opaShdr.outputs['BSDF'])
                    mat.node_tree.links.new(mixShdr.inputs[2], glasShdr.outputs['BSDF'])
                    mat.node_tree.links.new(mat.node_tree.nodes['Material Output'].inputs['Surface'],
                                            mixShdr.outputs['Shader'])

                    mat.blend_method = 'BLEND'
                    mat.shadow_method = 'HASHED'
                    mat.use_backface_culling = True
                    mat.show_transparent_back = False

                # append material
                mats.append(mat)

            for ii in range(0, cmf.SectionTable[i].MeshCount):  # Mesh

                vertArray = []
                faceArray = []
                matidArray = []
                maxBoneIDs = []

                for iii in range(0, cmf.SectionTable[i].mesh_geo[ii].MeshFaceSectionCount):  # Material ?
                    # print cmf.SectionTable[i].mesh_geo[ii].face_array[iii].count

                    maxBoneID = 0
                    for iiii in range(0, cmf.SectionTable[i].mesh_geo[ii].face_info[iii].FCount2):
                        if cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii] > maxBoneID:
                            maxBoneID = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]

                    append(maxBoneIDs, maxBoneID)
                    # format "%\t%\t%\n" ii iii maxBoneID

                    if cmf.SectionTable[i].mesh_geo[ii].face_info[iii].Ftype == 4:  # Triangle List
                        for iiii in range(0, cmf.SectionTable[i].mesh_geo[ii].face_info[iii].FCount2 / 3):
                            f1 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][(iiii * 3) + 0]
                            f2 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][(iiii * 3) + 1]
                            f3 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][(iiii * 3) + 2]
                            append(faceArray, (f1, f2, f3))
                            append(matidArray, (cmf.SectionTable[i].mesh_geo[ii].face_info[iii].MatNumber1))


                    elif cmf.SectionTable[i].mesh_geo[ii].face_info[iii].Ftype == 5:  # Triangle Strip
                        iiii = 0
                        StartDirection = -1
                        f1 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]
                        iiii += 1
                        f2 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]
                        iiii += 1
                        FaceDirection = StartDirection
                        while iiii < (cmf.SectionTable[i].mesh_geo[ii].face_info[iii].FCount2):
                            f3 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]
                            iiii += 1
                            if f3 == 0xFFFF or f3 == -1:
                                f1 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]
                                iiii += 1
                                f2 = cmf.SectionTable[i].mesh_geo[ii].face_array[iii][iiii]
                                iiii += 1
                                FaceDirection = StartDirection

                            else:
                                FaceDirection *= -1
                                if f1 != f2 and f2 != f3 and f3 != f1:
                                    if FaceDirection > 0:
                                        append(faceArray, (f1, f2, f3))

                                    else:
                                        append(faceArray, (f1, f3, f2))

                                    append(matidArray, cmf.SectionTable[i].mesh_geo[ii].face_info[iii].MatNumber1)

                                f1 = f2
                                f2 = f3




                    else:
                        print("Unsupported Face List [%i]" % (cmf.SectionTable[i].mesh_geo[ii].face_info[iii].Ftype))

                # print(cmf.SectionTable[i].mesh_geo[ii].MeshName + "\t" + cmf.SectionTable[i].mesh_mat[ii].Mattname)
                msh = mesh(
                    cmf.SectionTable[i].mesh_geo[ii].vertex_array,
                    faceArray,
                    matidArray,
                    cmf.SectionTable[i].mesh_geo[ii].texcoord_array,
                    cmf.SectionTable[i].mesh_geo[ii].normal_array if impNormals else [],
                    cmf.SectionTable[i].mesh_geo[ii].colour_array if impColours else [],
                    mats,
                    mscale,
                    True,
                    cmf.SectionTable[i].mesh_geo[ii].MeshName
                )
                # Parent Mesh to skeleton
                if msh != None and boneArray != None and boneArray.armature != None:
                    msh.parent = boneArray.armature

                    if impWeights:
                        
                        # apply a skin modifier
                        
                        skin = skinOps(msh, boneArray.armature, cmf.BoneParStrs[i])
                        #print(boneArray)
                        # assign bones to skin modifier, from the weight pallete
                        boneSkinned = []
                        for iii in range(0, cmf.BoneParInfo[i].BoneCount):  # Bones
                            boneID_index = findItem(usedBoneIds, cmf.BoneParInfo[i].childIds[iii])
                            
                            if boneID_index > -1:
                                append(boneSkinned, usedBoneNames[boneID_index])
                                skin.addbone(usedBoneNames[boneID_index], 0)
                        #print("usedBoneIds:\t%i" % len(boneSkinned))

                        # create a bonemap
                        
                        numBones = len(boneSkinned)#skin.GetNumberBones()
                        
                        if numBones != skin.GetNumberBones():
                            print("Fuuuuug, bones were deleted!")
                        
                        if numBones > 0:
                            # get names of bones in skin list
                            boneNames = []
                            boneNames = [str] * numBones
                            for iii in range(0, numBones):
                                boneNames[iii] = skin.GetBoneName(iii, 0)

                                # map boneArray to skin list
                                boneMap = []
                                boneMap = [int] * numBones
                                for iii in range(0, numBones):
                                    boneMap[iii] = 0  # default assignment to first bone in skin list
                                    boneID_index = findItem(boneNames, boneSkinned[iii])
                                    if boneID_index > -1: boneMap[iii] = boneID_index

                            c = 0
                            #print(numBones)
                            for iii in range(0, skin.GetNumberVertices()):
                                bi = []
                                bw = []
                                for iiii in range(0, len(cmf.SectionTable[i].mesh_geo[ii].weight_array[iii])):
                                    if cmf.SectionTable[i].mesh_geo[ii].weight_array[iii][iiii] > 0.0 and cmf.SectionTable[i].mesh_geo[ii].boneid_array[iii][iiii] != 255.0:
                                        boneID_index = int(
                                            cmf.SectionTable[i].mesh_geo[ii].boneid_array[iii][iiii] / 3.0
                                            )
                                        #if iii == 509 or iii == 883:
                                            #print(cmf.SectionTable[i].mesh_geo[ii].bonepal_array[c])
                                        try: boneID_index = cmf.SectionTable[i].mesh_geo[ii].bonepal_array[c][boneID_index]
                                        except: boneID_index = 0
                                        
                                        boneID_index = boneMap[boneID_index]
                                        append(bi, boneID_index)
                                        append(bw, cmf.SectionTable[i].mesh_geo[ii].weight_array[iii][iiii])

                                
                                skin.ReplaceVertexWeights(iii, bi, bw)
                                if iii == maxBoneIDs[c]: c += 1
                        bpy.context.view_layer.update()
    else: print("Failed To Open File")
    return None

# END OF MAIN FUNCTION ##############################################################

clearListener()  # clears out console
if not useOpenDialog:

    deleteScene(['MESH', 'ARMATURE'])  # Clear Scene
    read(
        "C:\\Users\\Corey\\Downloads\\research_test\\akiitm000_obj.bin"
    )
    messageBox("Done!")
else:
    wrapper1(True)
# bpy.context.scene.unit_settings.system = 'METRIC'

# bpy.context.scene.unit_settings.scale_length = 1.001
