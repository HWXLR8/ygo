#!/usr/bin/env python3

import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
import moderngl
import sqlite3
import numpy as np
from PIL import Image
import glm
import random
import getopt
import time
import uuid

from include.config import *
from include.network import Server, Client, Replay

SH_VERTEX = open("shaders/vertex.glsl").read()
SH_FRAGMENT = open("shaders/fragment.glsl").read()
SH_FRAGMENT_FOIL = open("shaders/fragment_foil.glsl").read()

class Graphic:
    def __init__(self, context, vertices,
                 texture, position, width, height, rotation):
        self.ctx = context
        self.x = position[0]
        self.y = position[1]
        self.z = position[2]
        self.r = 1.0
        self.g = 1.0
        self.b = 1.0
        self.a = 1.0
        self.width = width
        self.height = height
        self.rotation = rotation
        self.move_in_progress = False
        self.change_size_in_progress = False
        self.debug_counter = 0
        self.texture = texture
        if vertices is None:
            vertices = np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 0.0, 0.0, 1.0,
            1.0, 0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0,

            0.0, 1.0, 0.0, 0.0, 1.0,
            1.0, 1.0, 0.0, 1.0, 1.0,
            1.0, 0.0, 0.0, 1.0, 0.0,
        ], dtype='f4')
        self.prog = self.ctx.program(
            vertex_shader = SH_VERTEX,
            fragment_shader = SH_FRAGMENT,
        )
        self.time = 0.0
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert', 'in_text')
        self.illuminated = True
        self.visible = True

    def __del__(self):
        self.vao.release()
        self.vbo.release()
        self.prog.release()
        # not sure why this crashes
        # self.texture.release()

    def isActive(self):
        pos = self.getPos()
        x = pos[0]
        y = pos[1]
        width, height = self.getSize()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        return (x <= mouse_x <= x+width) and (y <= mouse_y <= y+height)

    def isVisible(self):
        return self.visible

    def setVisible(self):
        self.visible = True

    def setInvisible(self):
        self.visible = False

    def setShaders(self, vert, frag):
        self.prog = self.ctx.program(
            vertex_shader = vert,
            fragment_shader = frag,
        )
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert', 'in_text')

    def setVert(self, vert):
        self.vbo.write(vert)
        self.vao.release()
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert', 'in_text')

    def setColors(self, color):
        self.r, self.g, self.b, self.a = color

    def illuminate(self):
        self.illuminated = True
        self.setColors((1.0, 1.0, 1.0, 1.0))

    def fade(self):
        self.illuminated = False
        self.setColors((0.4, 0.4, 0.4, 1.0))

    def isIlluminated(self):
        return self.illuminated

    def getTexture(self):
        return self.texture

    def setTexture(self, texture):
        if self.texture != texture:
            self.texture = texture

    def getRotation(self):
        return self.rotation

    def setRotationX(self, angle):
        self.rotation = [angle, self.rotation[1], self.rotation[2]]

    def setRotationY(self, angle):
        self.rotation = [self.rotation[0], angle, self.rotation[2]]

    def setRotationZ(self, angle):
        self.rotation = [self.rotation[0], self.rotation[1], angle]

    def moveInProgress(self):
        return self.move_in_progress

    def changeSize(self, new_size, num_steps):
        if self.change_size_in_progress is False: # first animation step
            self.change_size_in_progress = True
            self.new_width = new_size[0]
            self.new_height = new_size[1]
            self.change_size_num_steps = num_steps
            self.width_growth_rate = (self.new_width - self.width) / num_steps
            self.height_growth_rate = (self.new_height - self.height) / num_steps
            self.remaining_growth_width = abs(self.new_width - self.width)
            self.remaining_growth_height = abs(self.new_height - self.height)

        self.remaining_growth_width -= abs(self.width_growth_rate)
        self.remaining_growth_height -= abs(self.height_growth_rate)

        if self.remaining_growth_width <= 0:
            self.width = self.new_width
        else:
            self.width += self.width_growth_rate

        if self.remaining_growth_height <= 0:
            self.height = self.new_height
        else:
            self.height += self.height_growth_rate

        if self.width == self.new_width and self.height == self.new_height:
            self.change_size_in_progress = False

    # only to be called if a card is already moving, used to change
    # its destination
    def recalculateMoveDestination(self, dest):
        self.dest = dest
        self.dest_x = dest[0]
        self.dest_y = dest[1]
        self.remaining_distance_x = abs(self.dest_x - self.x)
        self.remaining_distance_y = abs(self.dest_y - self.y)
        self.vx = (self.dest_x - self.x) / self.num_steps
        self.vy = (self.dest_y - self.y) / self.num_steps

    def move(self, dest, num_steps):
        if self.move_in_progress is False: # first animation step
            self.move_in_progress = True
            self.num_steps = num_steps
            self.dest = dest
            self.dest_x = dest[0]
            self.dest_y = dest[1]
            # these absolute distances are used to calculate whether an
            # animation has overshot its destination. These are required
            # because it is unknown whether the vx or vy are positive or
            # negative speeds
            self.remaining_distance_x = abs(self.dest_x - self.x)
            self.remaining_distance_y = abs(self.dest_y - self.y)
            self.vx = (self.dest_x - self.x) / num_steps
            self.vy = (self.dest_y - self.y) / num_steps

        # if there is only 1 step, skip animation
        if num_steps == 1:
            self.x = self.dest_x
            self.y = self.dest_y
            self.remaining_distance_x = 0
            self.remaining_distance_y = 0
            self.move_in_progress = False
            return

        if self.remaining_distance_x <= 0 and self.remaining_distance_y <= 0:
            self.x = self.dest_x
            self.y = self.dest_y
            self.move_in_progress = False
            return

        if self.remaining_distance_x - abs(self.vx) <= 0:
            self.x = self.dest_x
            self.remaining_distance_x = 0
        else:
            self.remaining_distance_x -= abs(self.vx)
            self.x += self.vx

        if self.remaining_distance_y - abs(self.vy) <= 0:
            self.y = self.dest_y
            self.remaining_distance_y = 0
        else:
            self.remaining_distance_y -= abs(self.vy)
            self.y += self.vy
        self.num_steps -= 1

    def rotate(self, angle):
        self.rotation += angle

    def getPos(self):
        return [self.x, self.y, self.z]

    def getSize(self):
        return [self.width, self.height]

    def render(self):
        if not self.visible:
            return
        self.texture.use()
        self.model = glm.mat4()
        self.model = glm.translate(self.model, glm.vec3(self.x, self.y, self.z))
        # move origin to the center, rotate about the center, move origin back to top left
        self.model = glm.translate(self.model, glm.vec3(0.5 * self.width, 0.5 * self.height, 0));
        self.model = glm.rotate(self.model, glm.radians(self.rotation[0]), glm.vec3(1.0, 0.0, 0.0));
        self.model = glm.rotate(self.model, glm.radians(self.rotation[1]), glm.vec3(0.0, 1.0, 0.0));
        self.model = glm.rotate(self.model, glm.radians(self.rotation[2]), glm.vec3(0.0, 0.0, 1.0));
        self.model = glm.translate(self.model, glm.vec3(-0.5 * self.width, -0.5 * self.height, 0));
        self.model = glm.scale(self.model, glm.vec3(self.width, self.height, 0))
        self.prog['model'].write(self.model)

        self.view = glm.mat4()
        self.prog['view'].write(self.view)

        self.projection = glm.ortho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -100, 100)
        self.prog['projection'].write(self.projection)

        if 'r' in self.prog:
            self.prog['r'] = self.r
            self.prog['g'] = self.g
            self.prog['b'] = self.b
            self.prog['a'] = self.a

        if 'time' in self.prog:
            self.prog['time'] = self.time

        self.vao.render()
        self.time += 1

    def update(self):
        if self.move_in_progress:
            self.move(self.dest, self.num_steps)
        if self.change_size_in_progress:
            self.changeSize((self.new_width, self.new_height), self.change_size_num_steps)
        self.render()

class Database():
    def __init__(self):
        self.conn = sqlite3.connect('sql/cards.db')
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def queryCardInfoByCardName(self, name):
        q = "SELECT * FROM cards WHERE card_name LIKE ? LIMIT 3"
        self.cursor.execute(q, ('%'+name+'%',))
        self.commit()
        result = [item for item in self.cursor.fetchall()]
        self.close()
        return result

    def queryCardInfoByID(self, passcode):
        q = "SELECT * FROM cards WHERE card_id=?"
        self.cursor.execute(q, (passcode,))
        self.commit()
        result = [item for item in self.cursor.fetchall()]
        self.close()
        if result:
            card_info = {
                "passcode" : result[0][0],
                "card_name" : result[0][1],
                "card_type" : result[0][2],
                "card_subtype" : result[0][3],
                "card_attribute" : result[0][4],
                "monster_type" : result[0][5],
                "monster_class" : result[0][6],
                "monster_level" : result[0][7],
                "monster_atk" : result[0][8],
                "monster_def" : result[0][9],
                "card_text" : result[0][10],
            }
            return card_info
        return None

class Card(Graphic):
    def __init__(self, ctx, id, passcode, player_num, textures):
        self.id = id
        self.passcode = passcode
        self.player_num = player_num
        self.card_info = Database().queryCardInfoByID(passcode)
        if player_num == 1:
            rotation = [0, 0, 0]
            if self.isFusion():
                self.x = COORD["p1"]["fusion_deck"][0]
                self.y = COORD["p1"]["fusion_deck"][1]
                self.location = "fusion_deck"
            else:
                self.x = COORD["p1"]["deck"][0]
                self.y = COORD["p1"]["deck"][1]
                self.location = "deck"
        elif player_num == 2:
            rotation = [0, 0, 180]
            if self.isFusion():
                self.x = COORD["p2"]["fusion_deck"][0]
                self.y = COORD["p2"]["fusion_deck"][1]
                self.location = "fusion_deck"
            else:
                self.x = COORD["p2"]["deck"][0]
                self.y = COORD["p2"]["deck"][1]
                self.location = "deck"
        self.z = 0
        self.width = FIELD_CARD_WIDTH
        self.height = FIELD_CARD_HEIGHT

        self.front_vert = np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, 0.0, 1.0,
            1.0, 0.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 1.0, 0.0, 0.0,

            0.0, 1.0, 1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 1.0, 1.0, 0.0,

        ], dtype='f4')
        self.back_vert = np.array([
            # x, y, z, tx, ty
            0.0, 0.0, 1.0, 1.0, 0.0,
            1.0, 0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 1.0, 1.0, 1.0,

            1.0, 0.0, 1.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 0.0, 1.0,
            0.0, 1.0, 1.0, 1.0, 1.0,

        ], dtype='f4')
        self.current_vert = "front"
        self.front_tex = textures.getByPasscode(passcode)
        self.back_tex = textures.card_back
        super().__init__(ctx, self.front_vert, self.front_tex, (self.x, self.y, self.z), self.width, self.height, rotation.copy())
        if self.isFoil():
            self.setShaders(SH_VERTEX, SH_FRAGMENT_FOIL)
        self.flip_in_progress = False
        self.position_change_in_progress = False
        self.tsuk_in_progress = False
        self.face_up = True
        self.in_atk_position = True


    def __str__(self):
        return (f"position: [{self.x}, {self.y}, {self.z}]\nrotation: {self.getRotation}")

    def isFoil(self):
        return self.passcode in [
            "77585513",
            "44763025",
        ]

    def getFrontTexture(self):
        return self.front_tex

    def getCardInfo(self):
        return self.card_info

    def getPasscode(self):
        return self.passcode

    def getID(self):
        return self.id

    def getOwner(self):
        return self.player_num

    def setOwner(self, player_num):
        self.player_num = player_num

    def inHand(self):
        return self.location == "hand"

    def onField(self):
        return self.location == "field"

    def inGY(self):
        return self.location == "gy"

    def inBanish(self):
        return self.location == "banish"

    def inDeck(self):
        return self.location == "deck"

    def inFusionDeck(self):
        return self.location == "fusion_deck"

    def isMonster(self):
        return self.card_info["card_type"] == "Monster"

    def isToken(self):
        return self.card_info["card_type"] == "Token"

    def getType(self):
        return self.card_info["card_type"]

    def getSubType(self):
        return self.card_info["card_subtype"]

    def getName(self):
        return self.card_info["card_name"]

    def getMonsterLevel(self):
        if not self.isMonster():
            return
        return self.card_info["monster_level"]

    def toZone(self, zone):
        if not self.isFaceUp():
            self.flip()
        self.location = "field"
        zone.occupy(self)
        self.move(zone.getCoord(), 10)
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 10)

    def toTopDeck(self):
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 20)
        if self.isFaceUp():
            self.flip()
        if not self.in_atk_position:
            self.changePosition()
        if self.player_num == 1:
            self.move(COORD["p1"]["deck"], 30)
        elif self.player_num == 2:
            self.move(COORD["p2"]["deck"], 30)
        self.location = "deck"

    def toZoneSet(self, zone):
        self.location = "field"
        zone.occupy(self)
        if self.isMonster():
            self.forceFaceDownDEF()
        else:
            self.forceFaceDownATK()
        self.move(zone.getCoord(), 10)
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 10)

    def toGY(self):
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 20)
        self.forceFaceUpATK()
        if self.player_num == 1:
            self.move(COORD["p1"]["gy"], 30)
        elif self.player_num == 2:
            self.move(COORD["p2"]["gy"], 30)
        self.location = "gy"

    def toFusionDeck(self):
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 20)
        self.forceFaceUpATK()
        if self.player_num == 1:
            self.move(COORD["p1"]["fusion_deck"], 30)
        elif self.player_num == 2:
            self.move(COORD["p2"]["fusion_deck"], 30)
        self.location = "fusion_deck"

    def banish(self):
        self.changeSize((FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT), 20)
        self.forceFaceUpATK()
        if self.player_num == 1:
            self.move(COORD["p1"]["banish"], 30)
        elif self.player_num == 2:
            self.move(COORD["p2"]["banish"], 30)
        self.location = "banish"

    # set card state with no animation
    def forceFaceDownDEF(self):
        if self.player_num == 1:
            self.setRotationX(180)
        self.setRotationZ(-90)
        self.in_atk_position = False
        self.face_up = False

    # set card state with no animation
    def forceFaceDownATK(self):
        if self.player_num == 2:
            self.setRotationZ(180)
        self.setRotationY(180)
        self.setRotationX(0)
        self.in_atk_position = True
        self.face_up = False

    # set card state with no animation
    def forceFaceUpATK(self):
        if self.player_num == 2:
            self.setRotationZ(180)
        else:
            self.setRotationZ(0)
        self.setRotationY(0)
        self.setRotationX(0)
        self.in_atk_position = True
        self.face_up = True

    def forceFaceUpDEF(self):
        if self.player_num == 2:
            self.setRotationZ(90)
        else:
            self.setRotationZ(-90)
        self.in_atk_position = False
        self.face_up = True

    def isFaceUp(self):
        return self.face_up

    def setLocation(self, location):
        self.location = location

    def getLocation(self):
        return self.location

    def isEffectMonster(self):
        return self.card_info["card_subtype"] == "Effect"

    def isMonster(self):
        return self.card_info["card_type"] == "Monster"

    def isSpellOrTrap(self):
        return self.card_info["card_type"] == "Spell" or self.card_info["card_type"] == "Trap"

    def isTrap(self):
        return self.card_info["card_type"] == "Trap"

    def isSpell(self):
        return self.card_info["card_type"] == "Spell"

    def isFusion(self):
        return self.card_info["card_subtype"] == "Fusion"

    def isRitualMonster(self):
        return self.card_info["card_subtype"] == "Ritual" and self.isMonster()

    def isFieldSpell(self):
        return self.card_info["card_subtype"] == "Field"

    def animationInProgress(self):
        return (self.flip_in_progress or
                self.move_in_progress or
                self.tsuk_in_progress or
                self.position_change_in_progress)

    def tsuk(self):
        if self.flip_in_progress:
            return
        if self.position_change_in_progress:
            return
        if not self.in_atk_position and self.face_up:
            self.flip()
            return
        self.tsuk_in_progress = True
        if self.face_up:
            self.rotation[0] += 9
            self.rotation[2] -= 4.5
        else:
            self.rotation[0] -= 9
            self.rotation[2] += 4.5
        if self.rotation[2] % 90 == 0:
            self.in_atk_position = not self.in_atk_position
            self.face_up = not self.face_up
            self.tsuk_in_progress = False

    def flip(self):
        if self.position_change_in_progress or self.tsuk_in_progress:
            return
        self.flip_in_progress = True
        if self.face_up:
            # f/u atk
            if self.in_atk_position:
                self.rotation[1] += 12
            # f/u def
            else:
                self.rotation[0] += 12
        else:
            # f/d atk
            if self.in_atk_position:
                self.rotation[1] -= 12
            # f/d def
            else:
                self.rotation[0] -= 12

        if ((self.in_atk_position and self.rotation[1] % 180 == 0) or
            (not self.in_atk_position and self.rotation[0] % 180 == 0)):
            self.face_up = not self.face_up # toggle boolean
            self.flip_in_progress = False

    def changePosition(self):
        if self.tsuk_in_progress:
            return
        self.position_change_in_progress = True
        if self.in_atk_position:
            if self.face_up:
                self.rotation[2] -= 10
            else:
                self.rotation[2] += 10
        else:
            if self.face_up:
                self.rotation[2] += 10
            else:
                self.rotation[2] -= 10
        if self.rotation[2] % 90 == 0:
            self.in_atk_position = not self.in_atk_position
            self.position_change_in_progress = False

    def update(self):
        rotx, roty, rotz = self.getRotation()
        if (rotx <= 90 and rotz <= -45) or roty <= 90:
            self.setTexture(self.front_tex)
            if self.current_vert != "front":
                self.current_vert = "front"
                self.setVert(self.front_vert)
        if (rotx > 90 and rotz <= -45) or roty > 90:
            self.setTexture(self.back_tex)
            if self.current_vert != "back":
                self.current_vert = "back"
            self.setVert(self.back_vert)

        if self.flip_in_progress:
            self.flip()
        if self.position_change_in_progress:
            self.changePosition()
        if self.tsuk_in_progress:
            self.tsuk()
        super().update()

    def inATKPosition(self):
        return self.in_atk_position

class Field():
    def __init__(self, ctx):
        # spell/trap zones
        self.p1_mzones = [
            SingleCardZone(ctx, 1, "m", 1, COORD["p1"]["m1"]),
            SingleCardZone(ctx, 2, "m", 1, COORD["p1"]["m2"]),
            SingleCardZone(ctx, 3, "m", 1, COORD["p1"]["m3"]),
            SingleCardZone(ctx, 4, "m", 1, COORD["p1"]["m4"]),
            SingleCardZone(ctx, 5, "m", 1, COORD["p1"]["m5"])
        ]
        self.p1_stzones = [
            SingleCardZone(ctx, 6, "st", 1, COORD["p1"]["st1"]),
            SingleCardZone(ctx, 7, "st", 1, COORD["p1"]["st2"]),
            SingleCardZone(ctx, 8, "st", 1, COORD["p1"]["st3"]),
            SingleCardZone(ctx, 9, "st", 1, COORD["p1"]["st4"]),
            SingleCardZone(ctx, 10, "st", 1, COORD["p1"]["st5"])
        ]
        # p2 zones reversed for mirroring effect
        self.p2_mzones = [
            SingleCardZone(ctx, 1, "m", 2, COORD["p2"]["m5"]),
            SingleCardZone(ctx, 2, "m", 2, COORD["p2"]["m4"]),
            SingleCardZone(ctx, 3, "m", 2, COORD["p2"]["m3"]),
            SingleCardZone(ctx, 4, "m", 2, COORD["p2"]["m2"]),
            SingleCardZone(ctx, 5, "m", 2, COORD["p2"]["m1"]),
        ]
        self.p2_stzones = [
            SingleCardZone(ctx, 6, "st", 2, COORD["p2"]["st5"]),
            SingleCardZone(ctx, 7, "st", 2, COORD["p2"]["st4"]),
            SingleCardZone(ctx, 8, "st", 2, COORD["p2"]["st3"]),
            SingleCardZone(ctx, 9, "st", 2, COORD["p2"]["st2"]),
            SingleCardZone(ctx, 10, "st", 2, COORD["p2"]["st1"]),
        ]
        self.p1_field_spell_zone = SingleCardZone(ctx, "fs", "fs", 1, COORD["p1"]["field_spell"])
        self.p2_field_spell_zone = SingleCardZone(ctx, "fs", "fs", 2, COORD["p2"]["field_spell"])
        self.token_id = uuid.uuid4().hex
        self.token_passcodes = [
            "73915052", # sheep token
            "29843092", # ojama green
            "29843093", # ojama yellow
            "29843094", # ojama black
        ]

    def getZoneByID(self, zone_id, player_num):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones:
            if zone.getID() == zone_id and zone.getOwner() == player_num:
                return zone

    def incrementCounter(self, zone):
        zone.incrementCounter()

    def decrementCounter(self, zone):
        zone.decrementCounter()

    def removeToken(self, zone):
        zone.clear()
        self.token_id = uuid.uuid4().hex

    def createToken(self, ctx, player_num, zone, textures, token_id):
        if token_id is not None:
            self.token_id = token_id
        token = Card(ctx, self.token_id, self.token_passcodes[zone.token_index], player_num, textures)
        token.move(zone.getCoord(), 1)
        token.forceFaceUpDEF()
        zone.occupy(token)
        self.token_id = uuid.uuid4().hex

    def nextTokenType(self, ctx, player_num, zone, textures, token_id):
        if zone.token_index == 3:
            zone.token_index = 0
        else:
            zone.token_index += 1
        self.removeToken(zone)
        self.createToken(ctx, player_num, zone, textures, token_id)

    def getActiveZone(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            if zone.isActive():
                return zone
        return None

    def animationInProgress(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            if zone.card is not None:
                if zone.card.animationInProgress():
                    return True
        return False

    def fade(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            card = zone.getCard()
            if card is not None:
                card.fade()

    def illuminate(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            card = zone.getCard()
            if card is not None:
                card.illuminate()

    def update(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            card = zone.getCard()
            if card is not None:
                card.update()
            zone.update()

    # returns false if no available zones
    def getFreeSTZone(self, player_num):
        if player_num == 1:
            zone_list = self.p1_stzones
        elif player_num == 2:
            zone_list = self.p2_stzones
        for zone in zone_list:
            if not zone.isOccupied():
                return zone
        return None

    def getFreeMZone(self, player_num):
        if player_num == 1:
            zone_list = self.p1_mzones
        elif player_num == 2:
            zone_list = self.p2_mzones
        for zone in zone_list:
            if not zone.isOccupied():
                return zone
        return None

    def getFreeFieldSpellZone(self, player_num):
        if player_num == 1:
            if not self.p1_field_spell_zone.isOccupied():
                return self.p1_field_spell_zone
        elif player_num == 2:
            if not self.p2_field_spell_zone.isOccupied():
                return self.p2_field_spell_zone
        return None

    def getActiveCard(self):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            card = zone.getCard()
            if card is not None:
                if card.isActive():
                    return card
        return None

    def getActiveCardByID(self, id):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            card = zone.getCard()
            if card is not None:
                if card.getID() == id:
                    return card
        return None

    def removeCard(self, card):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            if zone.card is card:
                zone.clear()
                return

    def getOccupiedZoneByCardID(self, card_id):
        for zone in self.p1_stzones + self.p1_mzones + self.p2_stzones + self.p2_mzones + [self.p1_field_spell_zone, self.p2_field_spell_zone]:
            if zone.getCard() is not None:
                if zone.getCard().getID() == card_id:
                    return zone

class SingleCardZone():
    def __init__(self, ctx, zone_id, zone_type, player_num, coord):
        self.zone_id = zone_id
        self.zone_type = zone_type
        self.owner = player_num
        self.coord = coord
        self.set_coord = (coord[0] + 0.5 * FIELD_CARD_WIDTH - 0.5 * FIELD_CARD_HEIGHT,
                          coord[1] + 0.5 * FIELD_CARD_HEIGHT - 0.5 * FIELD_CARD_WIDTH)
        self.card = None
        self.occupied = False
        self.rect = pygame.Rect(self.set_coord, (FIELD_CARD_HEIGHT, FIELD_CARD_WIDTH))
        self.token_index = 0
        self.vert = lambda c: np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
            0.0, 0.0, 1.0, c * 0.1, 0.0,

            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 1.0, 1.0, c * 0.1 + 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
        ], dtype='f4')
        self.zero_vert = np.array([
            # x, y, z, tx, ty
            0.0, 0.0, 0.0, 0, 0,
            0.0, 0.0, 0.0, 0, 0,
            0.0, 0.0, 0.0, 0, 0,

            0.0, 0.0, 0.0, 0, 0,
            0.0, 0.0, 0.0, 0, 0,
            0.0, 0.0, 0.0, 0,.0,
        ], dtype='f4')
        img_nums = Image.open("assets/nums.gif").convert('RGB')
        self.tex_nums = ctx.texture(img_nums.size, 3, img_nums.tobytes())
        self.tex_nums.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.counter = Graphic(ctx, self.zero_vert, self.tex_nums, coord, LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
        self.counter_num = 0

    def incrementCounter(self):
        if self.counter_num != 9:
            self.counter_num += 1

    def decrementCounter(self):
        if self.counter_num != 0:
            self.counter_num -= 1

    def getID(self):
        return self.zone_id

    def getZoneType(self):
        return self.zone_type

    def getOwner(self):
        return self.owner

    def getCoord(self):
        return self.coord

    def occupy(self, card):
        self.card = card
        self.occupied = True

    def isOccupied(self):
        return self.occupied

    def getCard(self):
        return self.card

    def clear(self):
        self.card = None
        self.occupied = False

    def isActive(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def update(self):
        if self.counter_num == 0:
            self.counter.setVert(self.zero_vert)
        else:
            self.counter.setVert(self.vert(self.counter_num))
        self.counter.update()

class MultiCardZone():
    def __init__(self, coord):
        self.cards = []
        self.num_cards_exposed = 1
        self.top_card_displacement = 0
        self.x = coord[0]
        self.y = coord[1]

    def fade(self):
        for card in self.cards:
            card.fade()

    def illuminate(self):
        for card in self.cards:
            card.illuminate()

    def getCardList(self):
        deck = []
        for card in self.cards:
            deck.append((card.id, card.getPasscode()))
        return deck

    # card_list is either a list of tuples (id, passcode) or a list of passcodes
    def loadFromList(self, card_list, textures):
        self.cards = []
        for card in card_list:
            if isinstance(card, tuple):
                id = card[0]
                passcode = card[1]
            else:
                id = uuid.uuid4().hex
                passcode = card
            card = Card(self.ctx, id, passcode, self.player_num, textures)
            self.addCard(card)

    def animationInProgress(self):
        for card in self.cards:
            if card.animationInProgress():
                return True
        return False

    def update(self):
        for card in self.cards:
            card.update()
            # if the cards are not spread
            if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
                card.setInvisible()
        # we cant make shit invisible until the new top card has
        # completeley covered the zone
        if len(self.cards) == 0:
            return
        if self.cards[-1].animationInProgress():
            # we show up to max of 6 cards in case there are tons of
            # cards moving into the zone (quick mill etc)
            for c in range(min(len(self.cards), 6)):
                self.cards[-c].setVisible()
        # top card is always visible
        self.cards[-1].setVisible()

    def addCard(self, card):
        self.cards.append(card)

    def removeCard(self, card):
        card_index = self.cards.index(card)
        if self.num_cards_exposed > 1:
            self.num_cards_exposed -= 1
            for c in range(len(self.cards)):
                if c > card_index:
                    pos = self.cards[c].getPos()
                    self.cards[c].move((pos[0] + FIELD_CARD_WIDTH, pos[1]), 5)
        self.cards.remove(card)

    def spread(self):
        if not (self.y < pygame.mouse.get_pos()[1] < self.y + FIELD_CARD_HEIGHT):
            return False
        if self.cards == []:
            return False
        if self.num_cards_exposed == len(self.cards):
            return False
        speed = FIELD_CARD_WIDTH / 2
        self.top_card_displacement += speed
        for card_num in range(self.num_cards_exposed):
            self.cards[-(card_num + 1)].setVisible()
            self.cards[-(card_num + 2)].setVisible()
            card = self.cards[-(card_num + 1)]
            card.move((card.getPos()[0] - speed, card.getPos()[1]), 1)
        if self.top_card_displacement == FIELD_CARD_WIDTH:
            self.top_card_displacement = 0
            self.num_cards_exposed += 1

    def collapse(self):
        if not (self.y < pygame.mouse.get_pos()[1] < self.y + FIELD_CARD_HEIGHT):
            return
        if self.cards == []:
            return
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            return
        if self.num_cards_exposed != len(self.cards):
            if self.num_cards_exposed == len(self.cards) - 1:
                self.cards[-(self.num_cards_exposed + 1)].setInvisible()
            elif self.num_cards_exposed <= len(self.cards) - 2:
                self.cards[-(self.num_cards_exposed + 1)].setInvisible()
                self.cards[-(self.num_cards_exposed + 2)].setInvisible()

        speed = FIELD_CARD_WIDTH / 2
        if self.top_card_displacement == 0:
            self.top_card_displacement = FIELD_CARD_WIDTH
            self.num_cards_exposed -= 1
        self.top_card_displacement -= speed
        for card_num in range(self.num_cards_exposed):
            card = self.cards[-(card_num + 1)]
            card.move((card.getPos()[0] + speed, card.getPos()[1]), 1)

    def fullyCollapse(self):
        self.num_cards_exposed = 1
        self.top_card_displacement = 0
        for card in self.cards:
            if not card.animationInProgress():
                card.move((self.x, self.y), 1)

    def getActiveCard(self):
        active_card = None
        for card in self.cards:
            if card.isActive():
                # the reason we continue the loop even after we find
                # the active card is because we want the top-most
                # active card, which resides the furthest into the
                # list
                active_card = card
        return active_card

    def getActiveCardByID(self, id):
        for card in self.cards:
            if card.getID() == id:
                return card
        return None

class MainDeck(MultiCardZone):
    def __init__(self, ctx, player_num, network, textures, passcode_list):
        self.ctx = ctx
        self.network = network
        if player_num == 1:
            self.coord = (COORD["p1"]["deck"][0], COORD["p1"]["deck"][1], 0)
            z_rot = 0
        elif player_num == 2:
            self.coord = (COORD["p2"]["deck"][0], COORD["p2"]["deck"][1], 0)
            z_rot = 180
        MultiCardZone.__init__(self, self.coord)
        self.player_num = player_num
        self.loadFromList(passcode_list, textures)
        self.dummy_top_card = Graphic(ctx, None, textures.card_back, self.coord, FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT, [0, 0, z_rot])
        self.vert = lambda c: np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
            0.0, 0.0, 1.0, c * 0.1, 0.0,

            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 1.0, 1.0, c * 0.1 + 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
        ], dtype='f4')
        self.zero_vert = np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0, 0,
            0.0, 0.0, 1.0, 0, 0,

            0.0, 1.0, 1.0, 0, 0,
            1.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0,.0,
        ], dtype='f4')
        img_nums = Image.open("assets/nums.gif").convert('RGB')
        self.tex_nums = ctx.texture(img_nums.size, 3, img_nums.tobytes())
        self.tex_nums.filter = (moderngl.NEAREST, moderngl.NEAREST)
        if player_num == 1:
            self.deck_count_digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p1"]["deck_count"], DECK_COUNT_DIGIT_WIDTH, DECK_COUNT_DIGIT_HEIGHT, [0, 0, 0])
            self.deck_count_digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["deck_count"][0] + DECK_COUNT_DIGIT_SPACING, COORD["p1"]["deck_count"][1], 0), DECK_COUNT_DIGIT_WIDTH, DECK_COUNT_DIGIT_HEIGHT, [0, 0, 0])
        if player_num == 2:
            self.deck_count_digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p2"]["deck_count"], DECK_COUNT_DIGIT_WIDTH, DECK_COUNT_DIGIT_HEIGHT, [0, 0, 0])
            self.deck_count_digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["deck_count"][0] + DECK_COUNT_DIGIT_SPACING, COORD["p2"]["deck_count"][1], 0), DECK_COUNT_DIGIT_WIDTH, DECK_COUNT_DIGIT_HEIGHT, [0, 0, 0])
        self.deck_count_digits = [
            self.deck_count_digit1,
            self.deck_count_digit2,
        ]
        self.shuffleRequired = False

    def getTopCard(self):
        return self.cards[-1]

    def sendToOpponent(self):
        if not NETPLAY:
            return
        deck = self.getCardList()
        data = {"DECK_UPDATE" : deck}
        self.network.send(data)

    def updateDeckCount(self):
        num = str(len(self.cards)).zfill(2)
        c = 0
        for d in num:
            self.deck_count_digits[c].setVert(self.vert(int(d)))
            c += 1

    # reimplementation to return None if deck is not spread
    def getActiveCard(self):
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            return
        return super().getActiveCard()

    # reimplementation to auto shuffle after fully collapsing
    def collapse(self):
        super().collapse()
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            self.cards[-self.num_cards_exposed].setInvisible()
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0 and self.shuffleRequired:
            self.shuffle()
            self.shuffleRequired = False

    # reimplementation to indicate when auto shuffling is needed
    def spread(self):
        result = super().spread()
        # super().spread() will return false if this is not the active multicard zone
        if result is not False:
            self.shuffleRequired = True

    # override to make cards invisible
    def addCard(self, card):
        card.setInvisible()
        self.cards.append(card)

    def getMain(self):
        return self.cards

    def draw(self):
        self.fullyCollapse()
        if self.cards == []:
            return None
        return self.cards.pop()

    def mill(self, gy):
        gy.fullyCollapse()
        self.fullyCollapse()
        card = self.cards.pop()
        card.forceFaceDownATK()
        card.flip()
        card.setLocation("gy")
        if self.player_num == 1:
            card.move(COORD["p1"]["gy"], 16)
        elif self.player_num == 2:
            card.move(COORD["p2"]["gy"], 16)
        gy.addCard(card)

    def shuffle(self):
        if self.cards == []:
            return
        self.fullyCollapse()
        random.shuffle(self.cards)
        if NETPLAY:
            self.sendToOpponent()

    def update(self):
        if self.cards == []:
            return None
        self.updateDeckCount()
        for d in self.deck_count_digits:
            d.update()
        for card in self.cards:
            if not card.animationInProgress():
                card.forceFaceUpATK()
        super().update()
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            self.dummy_top_card.update()

    def fade(self):
        super().fade()
        self.dummy_top_card.fade()

    def illuminate(self):
        super().illuminate()
        self.dummy_top_card.illuminate()

    def isEmpty(self):
        if self.cards == []:
            return True
        return False

class FusionDeck(MultiCardZone):
    def __init__(self, ctx, player_num, network, textures):
        self.player_num = player_num
        self.network = network
        self.ctx = ctx
        if player_num == 1:
            self.coord = (COORD["p1"]["fusion_deck"][0], COORD["p1"]["fusion_deck"][1], 0)
            z_rot = 0
        elif player_num == 2:
            self.coord = (COORD["p2"]["fusion_deck"][0], COORD["p2"]["fusion_deck"][1], 0)
            z_rot = 180
        MultiCardZone.__init__(self, self.coord)
        self.dummy_top_card = Graphic(ctx, None, textures.card_back, self.coord, FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT, [0, 0, z_rot])
        self.goat_fusion_passcodes = [
            "27134689", # Master of Oz
            "87751584", # Gatling Dragon
            "90140980", # Ojama King
            "13803864", # Mokey Mokey King
            "49868263", # Ryu Senshi
            "85684223", # Reaper on the Nightmare
            "80071763", # Dark Balter the Terrible
            "17881964", # Darkfire Dragon
            "58528964", # Flame Ghost
            "63519819", # TER
        ]
        id = uuid.uuid4().hex
        for passcode in self.goat_fusion_passcodes:
            for i in range(3):
                card = Card(ctx, id, passcode, player_num, textures)
                card.setLocation("fusion_deck")
                self.cards.append(card)
                id = uuid.uuid4().hex

        if player_num == 1:
            self.sendToOpponent()
        self.dummy_top_card = Graphic(ctx, None, textures.card_back, self.coord, FIELD_CARD_WIDTH, FIELD_CARD_HEIGHT, [0, 0, z_rot])

    def sendToOpponent(self):
        if not NETPLAY:
            return
        deck = self.getCardList()
        data = {"FUSION_DECK_UPDATE" : deck}
        self.network.send(data)

    # reimplementation to return None if deck is not spread
    def getActiveCard(self):
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            return
        return super().getActiveCard()

    def fade(self):
        super().fade()
        self.dummy_top_card.fade()

    def illuminate(self):
        super().illuminate()
        self.dummy_top_card.illuminate()

    def update(self):
        if self.cards == []:
            return None
        for card in self.cards:
            card.update()
        if self.num_cards_exposed == 1 and self.top_card_displacement == 0:
            self.dummy_top_card.update()

class YDKParser:
    def __init__(self, deck):
        self.main_deck = []
        self.fusion_deck = []
        self.side_deck = []
        self.current_deck = self.main_deck
        with open(deck, "r") as f:
            for line in f:
                if line.strip() == "#main":
                    continue
                elif line.strip() == "#extra":
                    self.current_deck = self.fusion_deck
                    continue
                elif line.strip() == "!side":
                    self.current_deck = self.side_deck
                    continue
                elif line == "\n":
                    continue
                passcode = line.strip()
                self.current_deck.append(passcode)

    def getMainDeck(self):
        return self.main_deck

    def getFusionDeck(self):
        return self.fusion_deck

    def getSideDeck(self):
        return self.side_deck

class Hand():
    def __init__(self, deck, player_num):
        self.deck = deck
        self.player_num = player_num
        self.cards = []
        if player_num == 1:
            self.y = COORD["p1"]["hand_y"]
        elif player_num == 2:
            self.y = COORD["p2"]["hand_y"]
        self.overlap = 0 # how much cards overlap each other

    def fade(self):
        for card in self.cards:
            card.fade()

    def illuminate(self):
        for card in self.cards:
            card.illuminate()

    def getCardList(self):
        cards = []
        for card in self.cards:
            cards.append((card.getID(), card.getPasscode()))
        return cards

    def sync(self, card_list):
        new_hand = []
        for new_card in card_list:
            new_card_id = new_card[0]
            for card in self.cards:
                if card.getID() == new_card_id:
                    new_hand.append(card)
        self.cards = new_hand
        self.quickRefresh()

    def shuffle(self):
        random.shuffle(self.cards)
        self.quickRefresh()

    def animationInProgress(self):
        for card in self.cards:
            if card.animationInProgress():
                return True
        return False

    def addCard(self, card):
        card.setVisible()
        old_location = card.getLocation()
        card.setLocation("hand")
        self.cards.append(card)
        if old_location == "field" and not card.inATKPosition():
            if self.player_num == 1:
                card.forceFaceUpATK()
            elif self.player_num == 2:
                card.forceFaceDownATK()
        card.changeSize((HAND_CARD_WIDTH, HAND_CARD_HEIGHT), 15)
        if card.isFaceUp() and old_location in ["deck", "gy", "banish"]:
            card.flip()
        if self.player_num == 1:
            self.refresh()
            if not card.isFaceUp():
                card.flip()
        elif self.player_num == 2:
            self.refresh()

    def remove(self, card):
        self.cards.remove(card)
        self.quickRefresh()

    # simple refresh method to be used for hand shuffle, and
    # compressing hand after playing a card
    def quickRefresh(self):
        c = 0
        if self.player_num == 1:
            offset = lambda c: ((c * (HAND_CARD_WIDTH - self.overlap)), self.y)
        elif self.player_num == 2:
            offset = lambda c: (((SCREEN_WIDTH - HAND_CARD_WIDTH - INFO_PANEL_CARD_WIDTH) - (c * (HAND_CARD_WIDTH - self.overlap))), self.y)
        num_cards = len(self.cards) - 1
        if num_cards >= 6:
            self.overlap = (HAND_CARD_WIDTH / num_cards) * (num_cards - 6)
        else:
            self.overlap = 0
        for card in self.cards:
            card.move(offset(c), 5)
            c += 1

    # complex refresh method to be used during drawing only
    def refresh(self):
        c = 0
        if self.player_num == 1:
            offset = lambda c: ((c * (HAND_CARD_WIDTH - self.overlap)), self.y)
        elif self.player_num == 2:
            offset = lambda c: (((SCREEN_WIDTH - HAND_CARD_WIDTH - INFO_PANEL_CARD_WIDTH) - (c * (HAND_CARD_WIDTH - self.overlap))), self.y)
        num_cards = len(self.cards) - 1
        if num_cards >= 6:
            self.overlap = (HAND_CARD_WIDTH / num_cards) * (num_cards - 6)
        else:
            self.overlap = 0
        for card in self.cards:
            if card == self.cards[-1]:
                card.move(offset(c), 30)
            else:
                if card.moveInProgress():
                    card.recalculateMoveDestination(offset(c))
                card.move(offset(c), 5)
            c += 1

    def getActiveCard(self):
        active_card = None
        for card in self.cards:
            if card.isActive():
                # the reason we continue the loop even after we find
                # the active card is because we want the top-most
                # active card, which resides the furthest into the
                # list
                active_card = card
        return active_card

    def getActiveCardByID(self, id):
        for card in self.cards:
            if card.getID() == id:
                return card
        return None

    def drawInProgress(self):
        for card in self.cards:
            if card.inMotion():
                return True
        return False

    def isEmpty(self):
        return self.cards == []

    def update(self):
        for card in self.cards:
            card.update()

class Player():
    def __init__(self, ctx, player_num, ydk, network, textures):
        self.player_num = player_num
        # if no YDK, we are probably waiting for it to arrive over the net, in
        # the meantime, init a MainDeck so we can populate it with cards via loadFromList
        if ydk is None:
            self.deck = MainDeck(ctx, player_num, network, textures, [])
        else:
            self.deck = MainDeck(ctx, player_num, network, textures, YDKParser(str(ydk)).getMainDeck())
            self.deck.shuffle()
        self.fusion_deck = FusionDeck(ctx, player_num, network, textures)
        self.hand = Hand(self.deck, player_num)
        self.lp = LP(ctx, player_num)
        if player_num == 1:
            self.gy = MultiCardZone(COORD["p1"]["gy"])
            self.banish = MultiCardZone(COORD["p1"]["banish"])
        elif player_num == 2:
            self.gy = MultiCardZone(COORD["p2"]["gy"])
            self.banish = MultiCardZone(COORD["p2"]["banish"])

    def fade(self):
        self.deck.fade()
        self.fusion_deck.fade()
        self.gy.fade()
        self.banish.fade()
        self.hand.fade()

    def illuminate(self):
        self.deck.illuminate()
        self.fusion_deck.illuminate()
        self.gy.illuminate()
        self.banish.illuminate()
        self.hand.illuminate()

    def animationInProgress(self):
        return (
            self.deck.animationInProgress() or
            self.fusion_deck.animationInProgress() or
            self.hand.animationInProgress() or
            self.gy.animationInProgress() or
            self.banish.animationInProgress() or
            self.lp.animationInProgress()
        )

    def update(self):
        self.lp.update()
        self.deck.update()
        self.gy.update()
        self.fusion_deck.update()
        self.banish.update()
        self.hand.update()

    def getPlayerNum(self):
        return self.player_num

class Audio():
    def __init__(self):
        self.draw = pygame.mixer.Sound('assets/sfx/CardMechanics/CardDealing/YGO_CardDealing-1.ogg')
        self.hand_shuffle = pygame.mixer.Sound('assets/sfx/CardMechanics/YGO_HandShuffle.ogg')
        self.activate = pygame.mixer.Sound('assets/sfx/SpellMechanics/YGO_PlayASpell_REV.ogg')
        self.summon = pygame.mixer.Sound('assets/sfx/CreatureMechanics/YGO_CreatureSpecialSummon_REV-OPT2.ogg')
        self.change_position = pygame.mixer.Sound('assets/sfx/CreatureMechanics/YGO_SwitchCreaturePosition.ogg')
        self.mill = pygame.mixer.Sound('assets/sfx/CardMechanics/CardDealing/YGO_CardDealing-8.ogg')
        self.activate = pygame.mixer.Sound('assets/sfx/CreatureMechanics/YGO_CreatureSummon_Powerful_REV.ogg')
        self.lp_decrease = pygame.mixer.Sound('assets/sfx/PlayerSounds/YGO_PlayerDamage-Opt1_trimmed.wav')
        self.lp_increase = pygame.mixer.Sound('assets/sfx/PlayerSounds/YGO_PlayerDamage-Opt2_trimmed.wav')
        self.change_phase = pygame.mixer.Sound('assets/sfx/MenuBeeps/YGO_MenuBeep-2.ogg')
        self.end_turn = pygame.mixer.Sound('assets/sfx/CreatureMechanics/YGO_CreatureSummon_Standard.ogg')


class PhaseTracker():
    def __init__(self, ctx):
        self.vert = lambda x, y: np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, x * 0.166666, y * 0.5 + 0.5,
            1.0, 0.0, 1.0, x * 0.166666 + 0.166666, y * 0.5,
            0.0, 0.0, 1.0, x * 0.166666, y * 0.5,

            0.0, 1.0, 1.0, x * 0.166666, y * 0.5 + 0.5,
            1.0, 1.0, 1.0, x * 0.166666 + 0.166666, y * 0.5 + 0.5,
            1.0, 0.0, 1.0, x * 0.166666 + 0.166666, y * 0.5,
        ], dtype='f4')
        img_phases = Image.open("assets/phases.gif").convert('RGB')
        self.tex_phases = ctx.texture(img_phases.size, 3, img_phases.tobytes())
        self.tex_phases.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.dp = Graphic(ctx, self.vert(0, 1), self.tex_phases, COORD["phases"], PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.sp = Graphic(ctx, self.vert(1, 0), self.tex_phases, (COORD["phases"][0] + PHASE_SPACING, COORD["phases"][1], 0), PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.m1 = Graphic(ctx, self.vert(2, 0), self.tex_phases, (COORD["phases"][0] + PHASE_SPACING * 2, COORD["phases"][1], 0), PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.bp = Graphic(ctx, self.vert(3, 0), self.tex_phases, (COORD["phases"][0] + PHASE_SPACING * 3, COORD["phases"][1], 0), PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.m2 = Graphic(ctx, self.vert(4, 0), self.tex_phases, (COORD["phases"][0] + PHASE_SPACING * 4, COORD["phases"][1], 0), PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.ep = Graphic(ctx, self.vert(5, 0), self.tex_phases, (COORD["phases"][0] + PHASE_SPACING * 5, COORD["phases"][1], 0), PHASE_WIDTH, PHASE_HEIGHT, [0, 0, 0])
        self.phases = [
            self.dp,
            self.sp,
            self.m1,
            self.bp,
            self.m2,
            self.ep,
        ]
        self.active_phase = 0

    def reset(self):
        self.active_phase = 0
        self.illuminatePhase()

    def nextPhase(self):
        if self.active_phase == 5:
            return
        audio.change_phase.play()
        self.active_phase += 1
        self.illuminatePhase()

    def previousPhase(self):
        if self.active_phase == 0:
            return
        audio.change_phase.play()
        self.active_phase -= 1
        self.illuminatePhase()

    def illuminatePhase(self):
        # turn off all the lights
        i = 0
        for p in self.phases:
            p.setVert(self.vert(i, 0))
            i += 1
        # turn on the active phase
        c = 0
        for p in self.phases:
            if c == self.active_phase:
                p.setVert(self.vert(c, 1))
            c += 1

    def update(self):
        for p in self.phases:
            p.render()

class LP():
    def __init__(self, ctx, player_num):
        self.vert = lambda c: np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
            0.0, 0.0, 1.0, c * 0.1, 0.0,

            0.0, 1.0, 1.0, c * 0.1, 1.0,
            1.0, 1.0, 1.0, c * 0.1 + 0.1, 1.0,
            1.0, 0.0, 1.0, c * 0.1 + 0.1, 0.0,
        ], dtype='f4')
        self.zero_vert = np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0, 0,
            0.0, 0.0, 1.0, 0, 0,

            0.0, 1.0, 1.0, 0, 0,
            1.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0,.0,
        ], dtype='f4')
        img_nums = Image.open("assets/nums.gif").convert('RGB')
        self.tex_nums = ctx.texture(img_nums.size, 3, img_nums.tobytes())
        self.tex_nums.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.delta = ""

        if player_num == 1:
            # lp digits
            self.digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p1"]["lp"], LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp"][0] + LP_DIGIT_SPACING, COORD["p1"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit3 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp"][0] + LP_DIGIT_SPACING * 2, COORD["p1"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit4 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp"][0] + LP_DIGIT_SPACING * 3, COORD["p1"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit5 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp"][0] + LP_DIGIT_SPACING * 4, COORD["p1"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            # delta digits
            self.delta_digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p1"]["lp_delta"], LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING, COORD["p1"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit3 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 2, COORD["p1"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit4 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 3, COORD["p1"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit5 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p1"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 4, COORD["p1"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
        elif player_num == 2:
            # lp digits
            self.digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p2"]["lp"], LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp"][0] + LP_DIGIT_SPACING, COORD["p2"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit3 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp"][0] + LP_DIGIT_SPACING * 2, COORD["p2"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit4 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp"][0] + LP_DIGIT_SPACING * 3, COORD["p2"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            self.digit5 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp"][0] + LP_DIGIT_SPACING * 4, COORD["p2"]["lp"][1], 0), LP_DIGIT_WIDTH, LP_DIGIT_HEIGHT, [0, 0, 0])
            # delta digits
            self.delta_digit1 = Graphic(ctx, self.zero_vert, self.tex_nums, COORD["p2"]["lp_delta"], LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit2 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING, COORD["p2"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit3 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 2, COORD["p2"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit4 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 3, COORD["p2"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
            self.delta_digit5 = Graphic(ctx, self.zero_vert, self.tex_nums, (COORD["p2"]["lp_delta"][0] + LP_DELTA_DIGIT_SPACING * 4, COORD["p2"]["lp_delta"][1], 0), LP_DELTA_DIGIT_WIDTH, LP_DELTA_DIGIT_HEIGHT, [0, 0, 0])
        self.digits = [
            self.digit1,
            self.digit2,
            self.digit3,
            self.digit4,
            self.digit5,
        ]
        self.delta_digits = [
            self.delta_digit1,
            self.delta_digit2,
            self.delta_digit3,
            self.delta_digit4,
            self.delta_digit5,
        ]
        self.lp = "8000"
        self.new_lp = "8000" # used for animation
        self.setLP(self.lp)
        self.animation_timer = 0
        self.animate = False
        self.update()

    def animationInProgress(self):
        return self.animate

    def addToDelta(self, delta):
        if len(self.delta) == 5:
            return
        self.delta += delta
        c = 0
        for d in self.delta:
            self.delta_digits[c].setVert(self.vert(int(d)))
            c += 1
        # fill the rest of the delta with blank spaces
        while c != 5:
            self.delta_digits[c].setVert(self.zero_vert)
            c += 1

    # lp : string
    def setLP(self, lp):
        c = -1 # traversing self.digits in reverse
        for d in reversed(lp):
            self.digits[c].setVert(self.vert(int(d)))
            c -= 1
        # fill the rest of the lp with blank spaces
        while c != -6:
            self.digits[c].setVert(self.zero_vert)
            c -= 1

    # op : '+' or '-'
    def executeDeltaOperation(self, op):
        if self.delta == '':
            return
        if op == '-':
            audio.lp_decrease.play()
            lp = str(int(self.lp) - int(self.delta))
            if int(lp) < 0:
                lp = "0"
        elif op == '+':
            audio.lp_increase.play()
            lp = str(int(self.lp) + int(self.delta))
            if int(lp) > 99999:
                lp = "99999"
        self.new_lp = lp
        self.lp = lp
        self.animateDigits()
        self.clearDelta()

    def clearDelta(self):
        self.delta = ""
        for d in self.delta_digits:
            d.setVert(self.zero_vert)

    def backspaceDelta(self):
        if len(self.delta) == 0:
            return
        self.delta = self.delta[:-1]
        self.addToDelta('')

    def animateDigits(self):
        if self.animation_timer == 0:
            self.animate = True
        # clear the lp meter
        for x in self.digits:
            x.setVert(self.zero_vert)
        # only animate the number of digits in the new lp
        for c in range(1, len(self.new_lp) + 1):
            self.digits[-c].setVert(self.vert(random.randrange(10)))
        self.animation_timer += 1
        if self.animation_timer == 30:
            self.animate = False
            self.animation_timer = 0
            self.setLP(self.new_lp)

    def update(self):
        if self.animate == True:
            self.animateDigits()
        for x in self.digits:
            x.render()
        for x in self.delta_digits:
            x.render()

class KeyCommand():
    def __init__(self):
        return

class TurnTracker():
    def __init__(self, ctx):
        img_arrow = Image.open("assets/arrow.gif").convert('RGB')
        self.tex_arrow = ctx.texture(img_arrow.size, 3, img_arrow.tobytes())
        self.tex_arrow.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.arrow = Graphic(ctx, None, self.tex_arrow, COORD["arrow"], ARROW_WIDTH, ARROW_HEIGHT, [0, 0, 0])
        self.rotation = 0
        self.target_rotation = 0
        self.animate = False

    def nextTurn(self):
        self.target_rotation += 180
        self.animate = True

    # switch arrow direction w/o animation or sound
    def forceNextTurn(self):
        self.rotation = 180
        self.target_rotation = 180
        self.arrow.setRotationZ(self.rotation)

    def animateArrow(self):
        self.rotation += 15
        self.arrow.setRotationZ(self.rotation)
        if self.rotation >= self.target_rotation:
            audio.end_turn.play()
            if self.rotation == 360:
                self.rotation = 0
                self.target_rotation = 0
            self.rotation = self.target_rotation
            self.animate = False

    def animationInProgress(self):
        return self.animate

    def update(self):
        if self.animate:
            self.animateArrow()
        self.arrow.render()

class Textures():
    def __init__(self, ctx):
        self.ctx = ctx
        card_back_img = Image.open("assets/blank_card_back.png")
        self.card_back = ctx.texture(card_back_img.size, 3, card_back_img.tobytes())
        card_back_img.close()
        self.cache = {}

    def isMeme(self):
        if not MEMES:
            return False
        else:
            return self.passcode in [
                "3136426",
                "33508719",
                "41420027",
                "55144522",
                "73915051",
                "71044499",
                "77585513",
                "62279055",
                "23171610",
                "5318639",
                "72892473",
            ]

    def getByPath(self, path):
        img = Image.open(path).convert("RGB")
        tex = self.ctx.texture(img.size, 3, img.tobytes())
        img.close()
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.cache[path] = tex
        return tex

    def getByPasscode(self, passcode):
        if passcode in self.cache:
            return self.cache[passcode]
        if self.isMeme():
            img = Image.open("assets/meme_cards/" + passcode + ".png").convert('RGB')
        else:
            img = Image.open("assets/card_images_denoised/" + passcode + ".webp")
        tex = self.ctx.texture(img.size, 3, img.tobytes())
        if TEXTURE_SMOOTHING:
            tex.build_mipmaps(0, 1)
            tex.filter = (moderngl.LINEAR_MIPMAP_NEAREST, moderngl.LINEAR)
        img.close()
        self.cache[passcode] = tex
        return tex

class Text():
    def __init__(self, ctx, textures):
        self.ctx = ctx
        self.zero_vert = np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0, 0,
            0.0, 0.0, 1.0, 0, 0,

            0.0, 1.0, 1.0, 0, 0,
            1.0, 1.0, 1.0, 0, 0,
            1.0, 0.0, 1.0, 0,.0,
        ], dtype='f4')
        self.vert = lambda c: np.array([
            # x, y, z, tx, ty
            0.0, 1.0, 1.0, c * (1/128), 1.0,
            1.0, 0.0, 1.0, c * (1/128) + (1/128), 0.0,
            0.0, 0.0, 1.0, c * (1/128), 0.0,

            0.0, 1.0, 1.0, c * (1/128), 1.0,
            1.0, 1.0, 1.0, c * (1/128) + (1/128), 1.0,
            1.0, 0.0, 1.0, c * (1/128) + (1/128), 0.0,
        ], dtype='f4')
        self.tex = textures.getByPath("assets/alphabet_uppercase.gif")
        self.perma_text = {}
        self.temp_text = {}

    def generate(self, text, position, storage_type, width=DEFAULT_TEXT_WIDTH, height=DEFAULT_TEXT_HEIGHT, spacing=DEFAULT_TEXT_SPACING):
        x = position[0]
        y = position[1]
        chargfx = []
        c = 0
        for char in text:
            vert = self.vert(ord(char.upper()))
            if char == " ":
                vert = self.zero_vert
            letter = Graphic(self.ctx, vert, self.tex, (x + spacing * c, y, 0),  width, height, [0, 0, 0])
            chargfx.append(letter)
            c += 1
        if storage_type == "perma":
            self.perma_text[text] = chargfx
        elif storage_type == "temp":
            self.temp_text[text] = chargfx

    def moveLine(self, line, coord):
        x, y = coord
        spacing = {**self.perma_text, **self.temp_text}[line][0].getSize()[0]
        c = 0
        for char in {**self.perma_text, **self.temp_text}[line]:
            char.move((x + spacing * c, y), 1)
            c += 1

    def getActiveLine(self):
        for key, value in {**self.perma_text, **self.temp_text}.items():
            for char in value:
                if char.isActive():
                    return key
        return None

    def clearPermaStorage(self):
        self.perma_text = {}

    def clearTempStorage(self):
        self.temp_text = {}

    def highlightLine(self, line, color):
        for key, value in {**self.perma_text, **self.temp_text}.items():
            for char in value:
                char.setColors((1, 1, 1, 1))
        for char in {**self.perma_text, **self.temp_text}[line]:
            char.setColors(color)

    def update(self):
        for key, value in {**self.perma_text, **self.temp_text}.items():
            for char in value:
                char.update()

class DeckEditor():
    def __init__(self, ctx, clock, textures, ydk):
        self.ctx = ctx
        self.clock = clock
        self.textures = textures
        self.main_deck = []
        self.fusion_deck = []
        self.side_deck = []
        self.search_str = ""
        self.fusion_deck_offset = 0
        self.side_deck_offset = 0
        self.scroll_offset = 0
        self.text = Text(ctx, textures)
        self.mag_card = Graphic(self.ctx, None, self.textures.getByPath("assets/ducc.png"), (PLAYMAT_WIDTH, 0, 0),
                            INFO_PANEL_CARD_WIDTH, INFO_PANEL_CARD_HEIGHT, [0, 0, 0])
        self.save_icon = Graphic(self.ctx, None, self.textures.getByPath("assets/icons/save.gif"), COORD["db"]["save_icon"],
                            DB_ICON_WIDTH, DB_ICON_HEIGHT, [0, 0, 0])
        # self.new_icon = Graphic(self.ctx, None, self.textures.getByPath("assets/icons/new.gif"), COORD["db"]["new_icon"],
        #                     DB_ICON_WIDTH, DB_ICON_HEIGHT, [0, 0, 0])
        self.text.generate("MAIN DECK", COORD["db"]["main_label"],
                           "perma", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
        self.text.generate("FUSION DECK", COORD["db"]["fusion_label"],
                           "perma", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
        self.text.generate("SIDE DECK", COORD["db"]["side_label"],
                           "perma", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
        if ydk is not None:
            self.loadNewDeck(ydk)
        self.active_result = -1
        self.mag_priority = "kb"
        if not os.path.exists('decks'):
            os.makedirs('decks')
        self.listDecksInDeckDir()

    def loadNewDeck(self, ydk):
        self.scroll_offset = 0
        self.main_deck = []
        self.fusion_deck = []
        self.side_deck = []
        for passcode in YDKParser(ydk).getMainDeck():
            self.main_deck.append(Card(self.ctx, uuid.uuid4().hex, passcode, 1, self.textures))
        for passcode in YDKParser(ydk).getFusionDeck():
            self.fusion_deck.append(Card(self.ctx, uuid.uuid4().hex, passcode, 1, self.textures))
        for passcode in YDKParser(ydk).getSideDeck():
            self.side_deck.append(Card(self.ctx, uuid.uuid4().hex, passcode, 1, self.textures))

    def listDecksInDeckDir(self):
        decks = os.listdir(DECK_DIR)
        x, y, z = COORD["db"]["deck_dir"]
        for deck in decks:
            self.text.generate(deck, (x, y), "perma", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
            y += DB_TEXT_HEIGHT + 2

    def sortDeck(self, deck):
        normal_monsters = []
        effect_monsters = []
        ritual_monsters = []
        spells = []
        traps = []
        for card in deck:
            if card.isMonster():
                if card.isRitualMonster():
                    ritual_monsters.append(card)
                elif card.isEffectMonster():
                    effect_monsters.append(card)
                else:
                    normal_monsters.append(card)
            elif card.isSpell():
                spells.append(card)
            elif card.isTrap():
                traps.append(card)
        ritual_monsters.sort(key = lambda x: (x.getMonsterLevel(), x.getName()), reverse=True)
        normal_monsters.sort(key = lambda x: (x.getMonsterLevel(), x.getName()), reverse=True)
        effect_monsters.sort(key = lambda x: (x.getMonsterLevel(), x.getName()), reverse=True)
        spells.sort(key = lambda x: (x.getSubType(), x.getName()))
        traps.sort(key = lambda x: x.getName())
        return ritual_monsters + effect_monsters + normal_monsters + spells + traps

    def update(self):
        self.calculateVerticalOffset()
        self.save_icon.update()
        # self.new_icon.update()
        # do we want to update mag card based on search results...
        if self.active_result >= 0 and len(self.results) != 0:
            passcode = str(self.results[self.active_result][0])
            if self.mag_priority == "kb":
                self.mag_card.setTexture(self.textures.getByPasscode(passcode))
        # ... or what we are hovering over?
        active_card = self.getActiveCard()
        if active_card is not None and self.mag_card.getTexture() != active_card.getTexture() and self.mag_priority == "mouse":
            self.mag_card.setTexture(active_card.getTexture())
        self.mag_card.update()

        self.main_deck = self.sortDeck(self.main_deck)
        self.fusion_deck = self.sortDeck(self.fusion_deck)
        self.side_deck = self.sortDeck(self.side_deck)
        for card in self.main_deck:
            x = COORD["db"]["main"][0] + ((self.main_deck.index(card) % 10) * DB_CARD_WIDTH)
            y = COORD["db"]["main"][1] + (DB_CARD_HEIGHT * int(self.main_deck.index(card) / 10)) + self.scroll_offset
            card.move((x, y), 1)
            card.update()
        for card in self.fusion_deck:
            x = COORD["db"]["fusion"][0] + ((self.fusion_deck.index(card) % 10) * DB_CARD_WIDTH)
            y = COORD["db"]["fusion"][1] + (DB_CARD_HEIGHT * int(self.fusion_deck.index(card) / 10)) + self.scroll_offset
            card.move((x, y + self.fusion_deck_offset), 1)
            card.update()
        for card in self.side_deck:
            x = COORD["db"]["side"][0] + ((self.side_deck.index(card) % 10) * DB_CARD_WIDTH)
            y = COORD["db"]["side"][1] + (DB_CARD_HEIGHT * int(self.side_deck.index(card) / 10)) + self.scroll_offset
            card.move((x, y + self.side_deck_offset), 1)
            card.update()
        self.text.moveLine("MAIN DECK", (COORD["db"]["main_label"][0], COORD["db"]["main_label"][1] + self.scroll_offset))
        self.text.moveLine("FUSION DECK", (COORD["db"]["fusion_label"][0], COORD["db"]["fusion_label"][1] + self.fusion_deck_offset + self.scroll_offset))
        self.text.moveLine("SIDE DECK", (COORD["db"]["side_label"][0], COORD["db"]["side_label"][1] + self.side_deck_offset + self.scroll_offset))
        self.text.update()
        pygame.display.flip()

    def getMatches(self):
        self.results = Database().queryCardInfoByCardName(self.search_str)
        ypos = DB_TEXT_HEIGHT * 2
        for card in self.results:
            self.text.generate(card[1], (20, ypos), "temp", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
            ypos += DB_TEXT_HEIGHT + 2
        if len(self.results) != 0 and self.active_result == -1:
            self.active_result = 0

    def getActiveCard(self):
        for card in self.main_deck + self.side_deck + self.fusion_deck:
            if card.isActive():
                return card
        return None

    def generateCardFromActiveResult(self):
        if self.active_result == -1:
            return None
        passcode = str(self.results[self.active_result][0])
        tex = self.textures.getByPasscode(passcode)
        card = Card(self.ctx, uuid.uuid4().hex, passcode, 1, self.textures)
        return card

    # figures out how much to push down fusion/side deck when main
    # deck exceeds 40 cards
    def calculateVerticalOffset(self):
        self.fusion_deck_offset = 0
        self.side_deck_offset = 0
        if len(self.main_deck) > 40:
            offset = int(((len(self.main_deck) - 1) - 40) / 10) + 1
            self.fusion_deck_offset += DB_CARD_HEIGHT * offset
            self.side_deck_offset += DB_CARD_HEIGHT * offset
        if len(self.fusion_deck) > 10:
            offset = int(((len(self.fusion_deck) - 1) - 10) / 10) + 1
            self.side_deck_offset += DB_CARD_HEIGHT * offset

    def scrollDown(self):
        side_deck_overflow = int((len(self.side_deck) - 1) / 10) * DB_CARD_HEIGHT
        if abs(self.scroll_offset) >= self.side_deck_offset + side_deck_overflow:
            return
        self.scroll_offset -= DB_SCROLL_RATE

    def scrollUp(self):
        if self.scroll_offset == 0:
            return
        self.scroll_offset += DB_SCROLL_RATE

    def addActiveCardToMainDeck(self):
        card = self.generateCardFromActiveResult()
        if card is None:
            return
        if card.isFusion() or card.isToken():
            return
        self.main_deck.append(card)

    def addActiveCardToFusionDeck(self):
        card = self.generateCardFromActiveResult()
        if card is None:
            return
        if not card.isFusion():
            return
        self.fusion_deck.append(card)

    def addActiveCardToSideDeck(self):
        card = self.generateCardFromActiveResult()
        if card is None:
            return
        if card.isFusion() or card.isToken():
            return
        self.side_deck.append(card)

    def removeActiveCard(self):
        active_card = self.getActiveCard()
        if active_card is None:
            return
        active_card_id = active_card.getID()
        locations = [self.main_deck,
                     self.fusion_deck,
                     self.side_deck]
        for location in locations:
            for card in location:
                if card.getID() == active_card_id:
                    location.remove(card)

    def saveDeck(self):
        f = open(DECK_DIR + "new_deck.ydk", 'w')
        f.write("#main\n")
        for card in self.main_deck:
            f.write(card.getPasscode() + "\n")
        f.write("\n#extra\n")
        for card in self.fusion_deck:
            f.write(card.getPasscode() + "\n")
        f.write("\n!side\n")
        for card in self.side_deck:
            f.write(card.getPasscode() + "\n")

    def processInput(self):
        # ignore any keystrokes while super is held down as to not interfere with window managers
        if pygame.key.get_pressed()[pygame.K_LSUPER] or pygame.key.get_pressed()[pygame.K_RSUPER]:
            return

        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                self.mag_priority = "mouse"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.save_icon.isActive():
                        self.saveDeck()
                    self.removeActiveCard()
                    # we are hovering over a deck name
                    active_line = self.text.getActiveLine()
                    if active_line is None:
                        return
                    if active_line[-4:] == ".ydk":
                        self.loadNewDeck(DECK_DIR + active_line)
                        self.text.highlightLine(active_line, (1, 0, 0, 1))
                elif event.button == 4:
                    self.scrollUp()
                elif event.button == 5:
                    self.scrollDown()
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                self.text.clearTempStorage()
                if event.key == pygame.K_BACKSPACE:
                    self.mag_priority = "kb"
                    self.search_str = self.search_str[:-1]
                elif event.key == pygame.K_DOWN:
                    self.mag_priority = "kb"
                    if self.active_result != len(self.results) - 1 :
                        self.active_result += 1
                elif event.key == pygame.K_UP:
                    self.mag_priority = "kb"
                    if self.active_result != -1:
                        self.active_result -= 1
                elif event.key == pygame.K_RETURN or (event.key == pygame.K_m and mods & pygame.KMOD_CTRL):
                    if self.active_result != -1:
                        self.addActiveCardToMainDeck()
                elif event.key == pygame.K_f and mods & pygame.KMOD_CTRL:
                    if self.active_result != -1:
                        self.addActiveCardToFusionDeck()
                elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
                    if self.active_result != -1:
                        self.addActiveCardToSideDeck()
                # regular keystroke
                else:
                    self.mag_priority = "kb"
                    self.search_str += event.unicode
                self.text.generate(self.search_str, COORD["db"]["search"], "temp", DB_TEXT_WIDTH, DB_TEXT_HEIGHT, DB_TEXT_SPACING)
                if len(self.search_str) > 1:
                    self.getMatches()

    def main(self):
        while True:
            self.processInput()
            self.clock.tick(60)
            self.ctx.clear(0.0, 0.0, 0.0)
            self.update()

class Duel():
    def __init__(self, **kwargs):
        # mixer must be initialized before pygame, reduces latency for some reason
        pygame.mixer.pre_init(48000, -16, 2, 64)
        pygame.init()
        pygame.mixer.quit()
        pygame.mixer.init(48000, -16, 2, 64)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        self.screen = pygame.display.set_mode((int(SCREEN_WIDTH), int(SCREEN_HEIGHT)), pygame.DOUBLEBUF | pygame.OPENGL, vsync = VSYNC)
        self.clock = pygame.time.Clock()
        self.ctx = moderngl.create_context()
        # self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.enable(moderngl.BLEND)
        self.textures = Textures(self.ctx)

        self.replay_mode = False
        self.server = False
        self.client = False
        self.ydk = None
        self.state_deck_editor = False
        self.parseCommandLineArguments()

        if self.state_deck_editor:
            self.deck_editor = DeckEditor(self.ctx, self.clock, self.textures, self.ydk)
            self.deck_editor.main()

        self.text = Text(self.ctx, self.textures)
        self.field = Field(self.ctx)
        self.network = None
        if NETPLAY:
            self.initNetwork()
            self.waitForConnection()
            self.p1 = Player(self.ctx, 1, self.ydk, self.network, self.textures)
            self.p2 = Player(self.ctx, 2, None, self.network, self.textures)
        else:
            self.p1 = Player(self.ctx, 1, self.ydk, self.network, self.textures)
            self.p2 = Player(self.ctx, 2, self.ydk, self.network, self.textures)
        self.mag_card = Graphic(self.ctx, None, self.textures.getByPath("assets/ducc.png"), (PLAYMAT_WIDTH, 0, 0),
                            INFO_PANEL_CARD_WIDTH, INFO_PANEL_CARD_HEIGHT, [0, 0, 0])
        self.phase_tracker = PhaseTracker(self.ctx)
        self.turn_tracker = TurnTracker(self.ctx)
        if self.client:
            # set opposing arrow direction for 1 player
            self.turn_tracker.forceNextTurn()
            self.turn_tracker.update()

        self.playmat = Graphic(self.ctx, None, self.textures.getByPath("assets/playmat.jpg"), COORD["playmat"], PLAYMAT_WIDTH, PLAYMAT_HEIGHT, [0, 0, 0])
        self.unresolved_commands = []
        self.illuminated_cards = []
        self.screen_needs_updating = True

    def initNetwork(self):
        if self.server:
            self.network = Server(6969)
            self.network.start()
        elif self.client:
            self.network = Client(self.server_ip, 6969)
            self.network.start()

    def waitForConnection(self):
        print("waiting to establish a network connection...")
        while not self.network.isConnected():
            time.sleep(0.1)
            continue

    def sendKeyCommand(self, key, active_card):
        # keys we want to send over the net
        send_keys = [
            'a',
            'e',
            'f',
            's',
            'd',
            'm',
            'g',
            'b',
            'n',
            'h',
            'c',
            'x',
            'p',
            't',
            '0','1','2','3','4','5','6','7','8','9',
            'backspace',
            '-', '+',
            'right', 'left',
        ]
        active_card_id = None
        # only send key commands if they are player 1's
        if key not in send_keys:
            return
        if active_card is not None:
            active_card_id = active_card.getID()
        data = {
            "KEY_COMMAND" : key,
            "ACTIVE_CARD_ID" : active_card_id
        }
        self.network.send(data)

    def sendMouseCommand(self, command, zone_id, active_card_id):
        data = {
            "MOUSE_COMMAND" : command,
            "ACTIVE_ZONE_ID" : zone_id,
            "ACTIVE_CARD_ID" : active_card_id,
        }
        self.network.send(data)

    def sendHandToOpponent(self):
        hand = self.p1.hand.getCardList()
        data = {"HAND_UPDATE" : hand}
        if NETPLAY:
            self.network.send(data)

    # this generic removal function removes a card from wherever it resides
    def removeCard(self, player, card):
        if card.onField():
            self.field.removeCard(card)
        elif card.inHand():
            player.hand.remove(card)
        elif card.inDeck():
            player.deck.removeCard(card)
        elif card.inGY():
            player.gy.removeCard(card)
        elif card.inFusionDeck():
            player.fusion_deck.removeCard(card)
        elif card.inBanish():
            player.banish.removeCard(card)

    def animationInProgress(self):
        return (self.p1.animationInProgress() or
                self.p2.animationInProgress() or
                self.field.animationInProgress() or
                self.turn_tracker.animationInProgress())

    def parseCommandLineArguments(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "esc:d:r:", ["deck-editor", "server", "client=", "deck=", "replay="])
        except getopt.GetoptError as err:
            print(err)
            self.quitGame()

        for opt, arg in opts:
            if opt in ("-e", "--deck-editor"):
                self.state_deck_editor = True
            elif opt in ("-s", "--server"):
                self.server = True
            elif opt in ("-c", "--client"):
                self.client = True
                self.server_ip = arg
            elif opt in ("-d", "--deck"):
                self.ydk = arg
            elif opt in ("-r", "--replay"):
                self.replay_mode = True
                self.replay_file = arg
        if self.ydk is None and self.state_deck_editor != True:
            print("please specify which deck you are using")
            self.quitGame()

    def getActiveCard(self, id=None):
        card_locations = [
            self.p1.deck,
            self.p2.deck,
            self.p1.fusion_deck,
            self.p2.fusion_deck,
            self.p1.hand,
            self.p2.hand,
            self.p1.gy,
            self.p2.gy,
            self.p1.banish,
            self.p2.banish,
            self.field,
        ]
        active_card = None
        for location in card_locations:
            if id is None:
                active_card = location.getActiveCard()
            else:
                active_card = location.getActiveCardByID(id)
            if active_card is not None:
                return active_card

    def processLocalInput(self, event):
        if event.type == QUIT:
            self.quitGame()

        # ignore any keystrokes while super is held down as to not interfere with window managers
        if pygame.key.get_pressed()[pygame.K_LSUPER] or pygame.key.get_pressed()[pygame.K_RSUPER]:
            return

        if event.type == pygame.ACTIVEEVENT:
            self.screen_needs_updating = True
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quitGame()

            key = None
            if event.key == pygame.K_a:
                key = 'a'
            elif event.key == pygame.K_d:
                key = 'd'
            elif event.key == pygame.K_e:
                key = 'e'
            elif event.key == pygame.K_f:
                key = 'f'
            elif event.key == pygame.K_r:
                key = 'r'
            elif event.key == pygame.K_s:
                key = 's'
            elif event.key == pygame.K_t:
                key = 't'
            elif event.key == pygame.K_m:
                key = 'm'
            elif event.key == pygame.K_g:
                key = 'g'
            elif event.key == pygame.K_b:
                key = 'b'
            elif event.key == pygame.K_n:
                key = 'n'
            elif event.key == pygame.K_p:
                key = 'p'
            elif event.key == pygame.K_h:
                key = 'h'
            elif event.key == pygame.K_c:
                key = 'c'
            elif event.key == pygame.K_z:
                key = 'z'
            elif event.key == pygame.K_x:
                key = 'x'
            elif event.key == pygame.K_0:
                key = '0'
            elif event.key == pygame.K_1:
                key = '1'
            elif event.key == pygame.K_2:
                key = '2'
            elif event.key == pygame.K_3:
                key = '3'
            elif event.key == pygame.K_4:
                key = '4'
            elif event.key == pygame.K_5:
                key = '5'
            elif event.key == pygame.K_6:
                key = '6'
            elif event.key == pygame.K_7:
                key = '7'
            elif event.key == pygame.K_8:
                key = '8'
            elif event.key == pygame.K_9:
                key = '9'
            elif event.key == pygame.K_BACKSPACE:
                key = 'backspace'
            elif event.key == pygame.K_MINUS or event.key == K_KP_MINUS:
                key = '-'
            elif event.key == pygame.K_PLUS or event.key == K_KP_PLUS or event.unicode == "+":
                key = '+'
            elif event.key == pygame.K_LEFT:
                key = 'left'
            elif event.key == pygame.K_RIGHT:
                key = 'right'

            if key:
                self.runKeyCommand(self.p1, key, None)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_command = None
            if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                if event.button == 4:
                    mouse_command = "fusion_collapse"
                elif event.button == 5:
                    mouse_command = "fusion_spread"
            elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                if event.button == 1:
                    mouse_command = "increment_counter"
                elif event.button == 3:
                    mouse_command = "decrement_counter"
            else:
                if event.button == 1:
                    mouse_command = "left_click"
                elif event.button == 3:
                    mouse_command = "next_token"
                elif event.button == 4:
                    mouse_command = "collapse"
                elif event.button == 5:
                    mouse_command = "spread"
            if mouse_command:
                self.runMouseCommand(self.p1, mouse_command, None, None)

        if self.getActiveCard() is not None:
            active_card = self.getActiveCard()
            # do not allow p1 to see p2 f/d cards
            if active_card.getOwner() == 2 and not active_card.isFaceUp():
                return
            if active_card.getFrontTexture() != self.mag_card.getTexture():
                self.mag_card.setTexture(active_card.getFrontTexture())
                self.screen_needs_updating = True

    def processAPICommands(self, commands, player):
        # this is not a replay, pull events from the network
        if commands is None:
            key = None
            commands = []
            done = False
            while not done:
                command = self.network.getLatestCommand()
                if command is not None:
                    commands.append(command)
                else:
                    done = True
            commands = self.unresolved_commands + commands
            self.unresolved_commands = []
            if commands == []:
                return

        for command in commands:
            if "KEY_COMMAND" in command:
                key = command["KEY_COMMAND"]
                active_card_id = command["ACTIVE_CARD_ID"]
                result = self.runKeyCommand(player, key, active_card_id)
                # if an overlap occurred
                if result is False:
                    self.unresolved_commands.append(command)
            if "MOUSE_COMMAND" in command:
                mouse_command = command["MOUSE_COMMAND"]
                active_zone_id = command["ACTIVE_ZONE_ID"]
                active_card_id = command["ACTIVE_CARD_ID"]
                self.runMouseCommand(player, mouse_command, active_zone_id, active_card_id)
            if "HAND_UPDATE" in command:
                new_hand = command["HAND_UPDATE"]
                player.hand.sync(new_hand)
                audio.hand_shuffle.play()
            if "DECK_UPDATE" in command:
                new_deck = command["DECK_UPDATE"]
                player.deck.loadFromList(new_deck, self.textures)
            if "FUSION_DECK_UPDATE" in command:
                new_deck = command["FUSION_DECK_UPDATE"]
                player.fusion_deck.loadFromList(new_deck, self.textures)

    def runMouseCommand(self, player, mouse_command, zone_id, active_card_id):
        # check whether left clicking so summon a token, or to illuminate existing card
        active_card = self.getActiveCard(active_card_id)
        if player.getPlayerNum() == 1 and mouse_command == "left_click":
            if active_card is None:
                mouse_command = "summon_token"
            else:
                mouse_command = "illuminate"

        if mouse_command in [
                "summon_token",
                "next_token",
                "increment_counter",
                "decrement_counter",
        ]:
            # command running locally
            if zone_id is None:
                zone = self.field.getActiveZone()
                if zone is None:
                    return
                # don't summon tokens to opponent's field
                if zone.getOwner() == 2:
                    return
            # command received over the network
            if zone_id is not None:
                zone = self.field.getZoneByID(zone_id, player.getPlayerNum())

        if mouse_command == "illuminate":
            if active_card is None:
                return
            # first click, shut off the lights
            if self.illuminated_cards == []:
                self.fadeEverything()
            if not active_card.isIlluminated():
                active_card.illuminate()
                self.illuminated_cards.append(active_card)
            elif active_card.isIlluminated() and active_card in self.illuminated_cards:
                active_card.fade()
                self.illuminated_cards.remove(active_card)
            # last click, turn on the lights
            if self.illuminated_cards == []:
                self.illuminateEverything()
            if player.getPlayerNum() == 1 and NETPLAY:
                self.sendMouseCommand("illuminate", None, active_card.getID())

        elif mouse_command == "summon_token" or mouse_command == "next_token":
            if zone.getZoneType() == "st" or zone.getZoneType() == "fs":
                return
            if mouse_command == "summon_token":
                self.field.createToken(self.ctx, player.getPlayerNum(), zone, self.textures, active_card_id)
                active_card_id = zone.getCard().getID()
                # only send mouse commands if they are player 1's
                if player.getPlayerNum() == 1 and NETPLAY:
                    self.sendMouseCommand("summon_token", zone.getID(), active_card_id)
            elif mouse_command == "next_token":
                if not zone.isOccupied():
                    return
                if not zone.getCard().isToken():
                    return
                self.field.nextTokenType(self.ctx, player.getPlayerNum(), zone, self.textures, active_card_id)
                # only send mouse commands if they are player 1's
                if player.getPlayerNum() == 1 and NETPLAY:
                    self.sendMouseCommand("next_token", zone.getID(), zone.getCard().getID())

        elif mouse_command == "increment_counter":
            self.field.incrementCounter(zone)
            if player.getPlayerNum() == 1 and NETPLAY:
                self.sendMouseCommand("increment_counter", zone.getID(), None)
        elif mouse_command == "decrement_counter":
            self.field.decrementCounter(zone)
            if player.getPlayerNum() == 1 and NETPLAY:
                self.sendMouseCommand("decrement_counter", zone.getID(), None)

        elif mouse_command == "collapse":
            self.p1.deck.collapse()
            self.p1.gy.collapse()
            self.p1.banish.collapse()
            self.p2.gy.collapse()
            self.p2.banish.collapse()

        elif mouse_command == "spread":
            self.p1.deck.spread()
            self.p1.gy.spread()
            self.p1.banish.spread()
            self.p2.gy.spread()
            self.p2.banish.spread()

        elif mouse_command == "fusion_collapse":
            self.p1.fusion_deck.collapse()

        elif mouse_command == "fusion_spread":
            self.p1.fusion_deck.spread()
        self.screen_needs_updating = True

    def illegalOverlap(self, key, active_card):
        # actions which start an animation, therefore is not ready for another action
        keys = [
            'a',
            'e',
            'f',
            's',
            'g',
            'b',
            'n',
            'h',
            'c',
            'x',
            'p',
            't',
        ]
        if active_card is None:
            if key == 'e' and self.turn_tracker.animationInProgress():
                return True
            else:
                return False
        if key in keys and active_card.animationInProgress():
            return True
        return False

    # player -> Player
    # key -> String (ex 'd' for draw)
    def runKeyCommand(self, player, key, active_card_id):
        active_card = self.getActiveCard(active_card_id)

        # don't let the opponent fuck with cards they don't own
        if active_card is not None:
            if player.getPlayerNum() != active_card.getOwner():
                active_card = None

        # drop player 1 overlaps, recurse player 2 overlaps
        if player.getPlayerNum() == 1 and self.illegalOverlap(key, active_card):
            return
        elif player.getPlayerNum() == 2 and self.illegalOverlap(key, active_card):
            return False

        free_stzone = self.field.getFreeSTZone(player.getPlayerNum())
        free_mzone = self.field.getFreeMZone(player.getPlayerNum())
        free_fszone = self.field.getFreeFieldSpellZone(player.getPlayerNum())

        # (t)op of deck
        if key == 't':
            if active_card is None:
                return
            if active_card.inDeck():
                return
            if active_card.isToken():
                return
            self.removeCard(player, active_card)
            if active_card.isFusion():
                active_card.toFusionDeck()
                return
            active_card.toTopDeck()
            player.deck.addCard(active_card)

        # (e)nd turn
        elif key == 'e':
            self.turn_tracker.nextTurn()
            self.phase_tracker.reset()


        # (left) previous phase
        elif key == 'left':
            self.phase_tracker.previousPhase()

        # (right) next phase
        elif key == 'right':
            self.phase_tracker.nextPhase()

        # lifepoint delta
        elif key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9' ]:
            player.lp.addToDelta(key)

        # (backspace) lifepoint delta
        elif key == 'backspace':
            player.lp.backspaceDelta()

        # (-) subtract lp delta
        elif key == '-':
            player.lp.executeDeltaOperation(key)

        # (+) add lp delta
        elif key == '+':
            player.lp.executeDeltaOperation(key)

        # (x) toggle face-up-atk/face-down-def
        elif key == 'x' and active_card is not None:
            if active_card.isToken():
                return
            if not active_card.onField():
                return
            if not active_card.isMonster():
                return
            active_card.tsuk()

        # (z) shuffle hand
        elif key == 'z':
            if player.hand.isEmpty():
                return
            audio.hand_shuffle.play()
            player.hand.shuffle()
            self.sendHandToOpponent()

        # (a)ctivate
        elif key == 'a' and active_card is not None:
            if free_stzone is None and active_card.inHand():
                return
            if active_card.isMonster():
                return
            if active_card.inDeck():
                return
            if active_card.inGY():
                return
            if active_card.inBanish():
                return
            if active_card.isFieldSpell() and free_fszone is None:
                return
            audio.activate.play()
            if active_card.inHand():
                self.removeCard(player, active_card)
                if active_card.isFieldSpell() and free_fszone is not None:
                    active_card.toZone(free_fszone)
                else:
                    active_card.toZone(free_stzone)
            elif active_card.onField():
                active_card.flip()

        # (f)lip
        elif key == 'f':
            if active_card is None:
                return
            if active_card.isToken():
                return
            if active_card.onField():
                if active_card.isMonster() and (active_card.inATKPosition()):
                    return
                active_card.flip()
            elif active_card.inHand():
                active_card.flip()

        # (s)et
        # for now, only setting cards from the hand is supported
        elif key == 's':
            if active_card is None:
                return
            if active_card.isToken():
                return
            if active_card.isFieldSpell() and free_fszone is None:
                return
            if active_card.isSpellOrTrap() and free_stzone is None:
                return
            if active_card.isMonster() and free_mzone is None:
                return
            if active_card.onField():
                return
            if not active_card.isFaceUp() and player.getPlayerNum() == 1:
                return
            self.removeCard(player, active_card)
            if active_card.isMonster():
                active_card.toZoneSet(free_mzone)
            elif active_card.isFieldSpell():
                active_card.toZoneSet(free_fszone)
            elif not active_card.isMonster():
                active_card.toZoneSet(free_stzone)

        # (d)raw
        elif key == 'd':
            if player.deck.isEmpty():
                return
            if player.deck.getTopCard().animationInProgress():
                return
            audio.draw.play()
            card = player.deck.draw()
            card.forceFaceDownATK()
            player.hand.addCard(card)

        # (p)ass card to oppoenent
        elif key == 'p':
            if active_card is not None:
                audio.draw.play()
                self.removeCard(player, active_card)
                if player.getPlayerNum() == 1:
                    active_card.setRotationZ(180)
                    active_card.setOwner(2)
                    self.p2.hand.addCard(active_card)
                elif player.getPlayerNum() == 2:
                    active_card.setRotationZ(0)
                    active_card.setOwner(1)
                    self.p1.hand.addCard(active_card)

        # (r) shuffle
        elif key == 'r':
            player.deck.shuffle()

        # (m)ill
        elif key == 'm':
            if player.deck.isEmpty():
                return
            audio.mill.play()
            player.deck.mill(player.gy)

        # to (g)raveyard
        elif key == 'g' and active_card is not None:
            if active_card.getLocation() == "gy":
                return
            if active_card.isToken():
                zone = self.field.getOccupiedZoneByCardID(active_card.getID())
                if zone is not None:
                    self.field.removeToken(zone)
            else:
                audio.mill.play()
                self.removeCard(player, active_card)
                active_card.toGY()
                player.gy.fullyCollapse()
                player.gy.addCard(active_card)
            if self.illuminated_cards != [] and active_card.isIlluminated():
                self.illuminateEverything()

        # (b)anish
        elif key == 'b' and active_card is not None:
            if active_card.getLocation() == "banish":
                return
            if active_card.isToken():
                return
            self.removeCard(player, active_card)
            audio.mill.play()
            active_card.banish()
            player.banish.fullyCollapse()
            player.banish.addCard(active_card)
            if self.illuminated_cards != [] and active_card.isIlluminated():
                self.illuminateEverything()

        # (n)ormal summon
        elif key == 'n':
            if active_card is None:
                return
            if free_mzone is None:
                return
            if active_card.onField():
                return
            if not active_card.isMonster():
                return
            if not active_card.isFaceUp() and player.getPlayerNum() == 1:
                return
            if active_card.isFusion():
                player.fusion_deck.fullyCollapse()
            audio.summon.play()
            self.removeCard(player, active_card)
            active_card.toZone(free_mzone)

        # to (h)and
        elif key == 'h' and active_card is not None:
            if active_card.isToken():
                return
            if active_card.inHand():
                return
            if active_card.isFusion():
                if active_card.inFusionDeck():
                    return
                self.removeCard(player, active_card)
                player.fusion_deck.fullyCollapse()
                player.fusion_deck.addCard(active_card)
                active_card.toFusionDeck()
            else:
                self.removeCard(player, active_card)
                player.hand.addCard(active_card)

        # (c)hange battle position
        elif key == 'c':
            if active_card is None:
                return
            if not active_card.onField():
                return
            if not active_card.isFaceUp():
                return
            if not active_card.isMonster() and not active_card.isToken():
                return
            audio.change_position.play()
            active_card.changePosition()

        if NETPLAY and player.getPlayerNum() == 1:
            self.sendKeyCommand(key, active_card)
        self.screen_needs_updating = True

    def fadeEverything(self):
        self.playmat.fade()
        self.field.fade()
        self.p1.fade()
        self.p2.fade()

    def illuminateEverything(self):
        self.playmat.illuminate()
        self.field.illuminate()
        self.p1.illuminate()
        self.p2.illuminate()
        self.illuminated_cards = []

    def update(self):
        self.playmat.render()
        self.phase_tracker.update()
        self.turn_tracker.update()
        self.field.update()
        self.p1.update()
        self.p2.update()
        self.text.update()
        self.mag_card.update()
        pygame.display.flip()

    def quitGame(self):
        print("") # as to not overwrite the fps
        if NETPLAY:
            self.network.close()
        pygame.quit()
        sys.exit()

    def mainLoop(self):
        while True:
            for event in pygame.event.get():
                self.processLocalInput(event)
            if NETPLAY:
                self.processAPICommands(None, self.p2)
            self.clock.tick(60)
            # print(self.getActiveCard())
            # print(pygame.mouse.get_pos())
            if PRINT_FPS:
                print(self.clock.get_fps(), end='\r')
            if self.animationInProgress() or self.screen_needs_updating:
                self.screen_needs_updating = False
                self.ctx.clear(0.0, 0.0, 0.0)
                self.update()


    def replayLoop(self):
        replay_events = Replay().loadReplay(self.replay_file)
        c = 0
        while True:
            if len(replay_events) == 0:
                self.quitGame()
            self.clock.tick(60)
            if c == 60:
                event = replay_events.pop(0)
                print(event)
                if event["PLAYER"] == 1:
                    self.processAPICommands([event], self.p1)
                elif event["PLAYER"] == 2:
                    self.processAPICommands([event], self.p2)
                c = 0
            c += 1
            self.ctx.clear(0.0, 0.0, 0.0)
            self.update()

    def start(self):
        if self.replay_mode:
            self.replayLoop()
        else:
            self.mainLoop()

if __name__ == "__main__":
    duel = Duel()
    audio = Audio()
    duel.start()
