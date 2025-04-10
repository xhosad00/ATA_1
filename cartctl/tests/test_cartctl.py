#!/usr/bin/env python3
"""
Example of usage/test of Cart controller implementation.
"""

import sys
import unittest
# from cartctl.cartctl.cartctl import CartCtl
from cartctl.cartctl import CartCtl
from cartctl.cartctl import Status as CartCtlStatus
from cartctl.cart import Cart, CargoReq, CartError
from cartctl.cart import Status as CartStatus
from cartctl.jarvisenv import Jarvis

def log(msg):
    "simple logging"
    print('  %s' % msg)

# Basic functions with no asserts
def add_load(c: CartCtl, cargo_req: CargoReq):
    log('%d: Requesting %s at %s' % \
        (Jarvis.time(), cargo_req, cargo_req.src))
    c.request(cargo_req)

def on_move(c: Cart):
    log('%d: Cart is moving %s->%s' % (Jarvis.time(), c.pos, c.data))

def on_load(c: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: loading: %s' % (Jarvis.time(), c.pos, cargo_req))
    log(c)
    cargo_req.context = "loaded"

def on_unload(c: Cart, cargo_req: CargoReq):
    log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), c.pos, cargo_req))
    log(c)
    cargo_req.context = "unloaded"

def createBasicCargo(src, dst, weight, name):
    req = CargoReq(src, dst, weight, name)
    req.onload = on_load
    req.onunload = on_unload
    return req
    
class TestCartRequests(unittest.TestCase):

    def test_happy_no_prio(self):
        "Happy-path with no priority cargo"
        print("")

        
        def on_move(c: Cart):
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), c.pos, c.data))
            self.assertEqual(CartStatus.MOVING, cart.status)
            self.assertFalse(cart.empty())  #during entire run, the cart should have some cargo

        def on_load(c: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            self.assertFalse(cart.empty())
            self.assertEqual(None, cargo_req.context)
            cargo_req.context = "loaded"
            if cargo_req.content == 'broccoli':
                self.assertEqual('A', c.pos)
                self.assertEqual(cargo_req.weight, c.load_sum())
            if cargo_req.content == 'carrot':
                self.assertEqual('B', c.pos)
            if cargo_req.content == 'daikon':
                self.assertEqual('C', c.pos)
            if cargo_req.content == 'onion':
                self.assertEqual('C', c.pos)

        def on_unload(c: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            self.assertEqual("loaded", cargo_req.context)
            cargo_req.context = "unloaded"
            if cargo_req.content == 'broccoli':
                self.assertEqual('B', c.pos)
            if cargo_req.content == 'carrot':
                self.assertEqual('C', c.pos)
            if cargo_req.content == 'daikon':
                self.assertEqual('A', c.pos)
            if cargo_req.content == 'onion':
                self.assertEqual('D', c.pos)

        def createBasicCargo(src, dst, weight, name):
            req = CargoReq(src, dst, weight, name)
            req.onload = on_load
            req.onunload = on_unload
            return req

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        broccoli = createBasicCargo('A', 'B', 30, 'broccoli')
        carrot = createBasicCargo('B', 'C', 100, 'carrot')
        daikon = createBasicCargo('C', 'A', 10, 'daikon')
        onion = createBasicCargo('C', 'D', 20, 'onion')

        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.plan(30, add_load, (ctl,carrot))
        Jarvis.plan(35, add_load, (ctl,daikon))
        Jarvis.plan(38, add_load, (ctl,onion))
        Jarvis.run()

        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual('unloaded', broccoli.context)
        self.assertEqual('unloaded', carrot.context)
        self.assertEqual('unloaded', daikon.context)
        self.assertEqual('unloaded', onion.context)
        self.assertEqual(cart.pos, 'A')


    def test_happy_prio(self):
        "Happy-path with priority cargo"
        print("\n")

        def on_move(c: Cart):
            log('%d: Cart is moving %s->%s' % (Jarvis.time(), c.pos, c.data))
            self.assertEqual(CartStatus.MOVING, cart.status)

        def on_load(c: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: loading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            self.assertFalse(cart.empty())
            self.assertEqual(None, cargo_req.context)
            cargo_req.context = "loaded"

        def on_unload(c: Cart, cargo_req: CargoReq):
            log('%d: Cart at %s: unloading: %s' % (Jarvis.time(), c.pos, cargo_req))
            log(c)
            cargo_req.context = "unloaded"
            if cargo_req.content == 'carrot':
                self.assertEqual('B', c.pos)
                self.assertEqual(0, c.load_sum()) # check that daikon wasnt loaded (Unload_Only)

        def createBasicCargo(src, dst, weight, name):
            req = CargoReq(src, dst, weight, name)
            req.onload = on_load
            req.onunload = on_unload
            return req
        
        def checkUNLOAD_ONLY(ctl):
            self.assertEqual(CartCtlStatus.UNLOAD_ONLY, ctl.status)

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)
        
        broccoli = createBasicCargo('B', 'D', 150, 'broccoli')
        carrot = createBasicCargo('D', 'B', 30, 'carrot')
        daikon = createBasicCargo('A', 'B', 40, 'daikon')

        Jarvis.reset_scheduler()
        Jarvis.plan(1, add_load, (ctl,broccoli))
        Jarvis.plan(2, add_load, (ctl,carrot))
        Jarvis.plan(70, add_load, (ctl,daikon))
        Jarvis.plan(90, checkUNLOAD_ONLY, (ctl,))
        Jarvis.run()

        # # Verify direct output
        log(cart)
        self.assertTrue(cart.empty())
        self.assertEqual('unloaded', broccoli.context)
        self.assertEqual('unloaded', carrot.context)
        self.assertEqual('unloaded', daikon.context)
        # self.assertEqual(cart.pos, 'D')

    def test_optimize_total_path(self):
        """Require good path optimization"""
        # optimezed path:           A->B->C->D->A 70
        # worse path (due to UCS):  A->B->A->B->C->D

        cart = Cart(4, 150, 0)
        cart.onmove = on_move
        ctl = CartCtl(cart, Jarvis)

        broccoli = createBasicCargo('A', 'B', 20, 'broccoli')
        carrot = createBasicCargo('B', 'A', 30, 'carrot')
        daikon = createBasicCargo('B', 'D', 40, 'daikon')
        Jarvis.reset_scheduler()
        Jarvis.plan(1, add_load, (ctl,broccoli))
        Jarvis.plan(2, add_load, (ctl,carrot))
        Jarvis.plan(3, add_load, (ctl,daikon))
        Jarvis.run()
        self.assertEqual(cart.pos, 'A')

        cart = Cart(4, 150, 0)
        ctl = CartCtl(cart, Jarvis)

    def test_cart_props_slots(self):
        """test cart slot restrtictions"""
        # "C-01 The cart shall have a capacity of 1 to 4 slots"
        Cart(1, 150, 0)
        Cart(2, 150, 0)
        Cart(3, 150, 0)
        Cart(4, 150, 0)
        self.assertRaises(CartError, Cart, 0, 50, 0)
        self.assertRaises(CartError, Cart, 5, 50, 0)

        # C-03 Carts with the lowest capacity shall have at least 2 slots
        self.assertRaises(CartError, Cart, 1, 50, 0)

        # C-04 Carts with the highest capacity shall not have more than 2 slots.
        Cart(1, 500, 0)
        Cart(2, 500, 0)
        self.assertRaises(CartError, Cart, 3, 500, 0)

    def test_cart_props_weight(self):
        """test cart weight restrtictions"""
        # C-02 The cart’s maximum capacity shall correspond to its type (50kg, 150 kg, or 500 kg).
        Cart(2, 50, 0)
        Cart(2, 150, 0)
        Cart(2, 500, 0)
        self.assertRaises(CartError, Cart, 2, 0, 0)
        self.assertRaises(CartError, Cart, 2, 1, 0)
        self.assertRaises(CartError, Cart, 2, 200, 0)
        self.assertRaises(CartError, Cart, 2, 501, 0)
        self.assertRaises(CartError, Cart, 2, 99.9, 0)

    def test_cart_props_bad_req(self):
        """test cart bad requests restrtictions"""
        # C-05 The control system shall not submit invalid requests (e.g.,cargo transfer exceeding the cart’s capacity).
        def add_load(c: CartCtl, cargo_req: CargoReq):
            c.request(cargo_req)

        def add_load_err(c: CartCtl, cargo_req: CargoReq):
            self.assertRaises(CartError, c.request, cargo_req)

        cart = Cart(2, 500, 0)
        ctl = CartCtl(cart, Jarvis)

        
        broccoli = CargoReq('A', 'D', 50, 'broccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli))
        Jarvis.run()
        
        # Ok
        cart = Cart(2, 500, 0)
        ctl = CartCtl(cart, Jarvis)        
        bigBroccoli = CargoReq('A', 'D', 1000, 'bigBroccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load_err, (ctl,bigBroccoli))
        Jarvis.run()
        
        # Should throw errors
        cart = Cart(2, 500, 0)
        ctl = CartCtl(cart, Jarvis)        
        negativeBroccoli = CargoReq('A', 'D', -1, 'bigBroccoli')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load_err, (ctl,negativeBroccoli))
        Jarvis.run()

        # F-10 is badly worded, needs clarification
        cart = Cart(2, 500, 1)
        cart.onmove = on_move
        broccoli1 = createBasicCargo('B', 'D', 50, 'broccoli1')
        broccoli2 = createBasicCargo('B', 'D', 50, 'broccoli2')
        broccoli3 = createBasicCargo('B', 'D', 50, 'broccoli3')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli1))
        Jarvis.plan(1, add_load, (ctl,broccoli2))
        Jarvis.plan(2, add_load_err, (ctl,broccoli3))
        Jarvis.run()

        # F-10 is badly worded, needs clarification
        cart = Cart(2, 500, 1)
        cart.onmove = on_move
        broccoli1 = createBasicCargo('B', 'D', 50, 'broccoli1')
        broccoli2 = createBasicCargo('B', 'D', 50, 'broccoli2')
        broccoli3 = createBasicCargo('B', 'D', 50, 'broccoli3')
        Jarvis.reset_scheduler()
        Jarvis.plan(0, add_load, (ctl,broccoli1))
        Jarvis.plan(1, add_load, (ctl,broccoli2))
        Jarvis.plan(35, add_load_err, (ctl,broccoli3))
        Jarvis.run()
        

        # C-06 The system shall communicate correctly with the factory’s external systems and respond to their requests.
        #TODO
        return
    

if __name__ == "__main__":
    unittest.main()
