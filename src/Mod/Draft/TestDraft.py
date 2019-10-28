"""Unit test for the Draft module.

From the terminal, run the following:
FreeCAD --run-test TestDraft

From within FreeCAD, run the following:
import Test, TestDraft
Test.runTestsFromModule(TestDraft)
"""
# ***************************************************************************
# *   (c) 2013 Yorik van Havre <yorik@uncreated.net>                        *
# *   (c) 2019 Eliud Cabrera Castillo                                       *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

# ===========================================================================
# First the command to run the test from the operating system terminal,
# followed by the command to run a test from the Python command line.
#
# ===========================================================================
# Run all Draft tests
# ----
# FreeCAD --run-test TestDraft
#
# import Test, TestDraft
# Test.runTestsFromModule(TestDraft)
#
# ===========================================================================
# Run tests from a module
# ----
# FreeCAD --run-test TestDraft
#
# import Test, TestDraft
# Test.runTestsFromModule(TestDraft)
#
# ===========================================================================
# Run tests from a class
# ----
# FreeCAD --run-test TestDraft.DraftCreation
#
# import Test, TestDraft
# Test.runTestsFromClass(TestDraft.DraftCreation)
#
# ===========================================================================
# Run a specific test
# ----
# FreeCAD --run-test TestDraft.DraftCreation.test_line
#
# import unittest
# one_test = "TestDraft.DraftCreation.test_line"
# all_tests = unittest.TestLoader().loadTestsFromName(one_test)
# unittest.TextTestRunner().run(all_tests)
# ===========================================================================

import unittest
import FreeCAD as App
import FreeCADGui as Gui
import Draft
from FreeCAD import Vector


def _msg(text):
    App.Console.PrintMessage("{}\n".format(text))


def _log(text):
    App.Console.PrintLog("{}\n".format(text))


def _draw_header():
    _msg("\n"
         "{0}".format(78*"-"))


def _import_test(module):
    _msg("  Try importing '{0}'".format(module))
    try:
        imported = __import__("{0}".format(module))
    except ImportError as exc:
        imported = False
        _msg("  {0}".format(exc))
    return imported


def _no_GUI(module):
    _msg("  ###---------------------------------------------------###\n"
         "  #    No GUI; cannot test for '{0}'\n"
         "  ###---------------------------------------------------###\n"
         "  Automatic PASS".format(module))


def _no_TEST():
    _msg("  ###---------------------------------------------------###\n"
         "  #    This test is not implemented currently             #\n"
         "  ###---------------------------------------------------###\n"
         "  Automatic PASS")


def _fake_func(p1=None, p2=None, p3=None, p4=None, p5=None):
    _no_TEST()
    return True


class DraftImport(unittest.TestCase):
    """Import the Draft modules."""
    # No document is needed to test 'import Draft' or other modules
    # thus 'setUp' just draws a line, and 'tearDown' isn't defined.
    def setUp(self):
        _draw_header()

    def test_import_Draft(self):
        """Import the Draft module."""
        module = "Draft"
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_Draft_geomutils(self):
        """Import Draft geometrical utilities."""
        module = "DraftGeomUtils"
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_Draft_vecutils(self):
        """Import Draft vector utilities."""
        module = "DraftVecUtils"
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_Draft_SVG(self):
        """Import Draft SVG utilities."""
        module = "getSVG"
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))


class DraftGuiImport(unittest.TestCase):
    """Import the Draft graphical modules."""
    # No document is needed to test 'import DraftGui' or other modules
    # thus 'setUp' just draws a line, and 'tearDown' isn't defined.
    def setUp(self):
        _draw_header()

    def test_import_GUI_DraftGui(self):
        """Import Draft TaskView GUI tools."""
        module = "DraftGui"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_Draft_snap(self):
        """Import Draft snapping."""
        module = "DraftSnap"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_Draft_tools(self):
        """Import Draft graphical commands."""
        module = "DraftTools"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_Draft_trackers(self):
        """Import Draft tracker utilities."""
        module = "DraftTrackers"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))


class DraftImportTools(unittest.TestCase):
    """Test for each individual module that defines a tool."""
    # No document is needed to test 'import' of other modules
    # thus 'setUp' just draws a line, and 'tearDown' isn't defined.
    def setUp(self):
        _draw_header()

    def test_import_GUI_DraftEdit(self):
        """Import Draft Edit."""
        module = "DraftEdit"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_DraftFillet(self):
        """Import Draft Fillet."""
        module = "DraftFillet"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_DraftLayer(self):
        """Import Draft Layer."""
        module = "DraftLayer"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_GUI_DraftPlane(self):
        """Import Draft SelectPlane."""
        module = "DraftSelectPlane"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_import_WorkingPlane(self):
        """Import Draft WorkingPlane."""
        module = "WorkingPlane"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))


class DraftPivy(unittest.TestCase):
    """Test for the presence of Pivy and that it works with Coin3d."""

    def setUp(self):
        """Set up a new document to hold the tests.

        It is executed before every test, so we create a document
        to hold the objects.
        """
        _draw_header()
        self.doc_name = self.__class__.__name__
        if App.ActiveDocument:
            if App.ActiveDocument.Name != self.doc_name:
                App.newDocument(self.doc_name)
        else:
            App.newDocument(self.doc_name)
        App.setActiveDocument(self.doc_name)
        self.doc = App.ActiveDocument
        _msg("  Temporary document '{0}'".format(self.doc_name))

    def test_Pivy(self):
        """Import Pivy Coin."""
        module = "pivy.coin"
        imported = _import_test(module)
        self.assertTrue(imported, "Problem importing '{0}'".format(module))

    def test_Pivy_draw(self):
        """Use Coin (pivy.coin) to draw a cube on the active view."""
        module = "pivy.coin"
        if not App.GuiUp:
            _no_GUI(module)
            self.assertTrue(True)
            return

        import pivy.coin
        cube = pivy.coin.SoCube()
        _msg("  Draw cube")
        Gui.ActiveDocument.ActiveView.getSceneGraph().addChild(cube)
        _msg("  Adding cube to the active view scene")
        self.assertTrue(cube, "Pivy is not working properly.")

    def tearDown(self):
        App.closeDocument(self.doc_name)


class DraftCreation(unittest.TestCase):
    """Test Draft creation functions."""

    def setUp(self):
        """Set up a new document to hold the tests.

        It is executed before every test, so we create a document
        to hold the objects.
        """
        _draw_header()
        self.doc_name = self.__class__.__name__
        if App.ActiveDocument:
            if App.ActiveDocument.Name != self.doc_name:
                App.newDocument(self.doc_name)
        else:
            App.newDocument(self.doc_name)
        App.setActiveDocument(self.doc_name)
        self.doc = App.ActiveDocument
        _msg("  Temporary document '{0}'".format(self.doc_name))

    def test_line(self):
        """Create a line."""
        func = "Draft Line"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeLine(Vector(0, 0, 0),
                             Vector(2, 0, 0))
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_polyline(self):
        """Create a polyline."""
        func = "Draft Wire"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeWire([Vector(0, 0, 0),
                              Vector(2, 0, 0),
                              Vector(2, 2, 0)])
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_fillet(self):
        """Create a fillet between two lines."""
        func = "Draft Fillet"
        _msg("  Test '{0}'".format(func))
        L1 = Draft.makeLine(Vector(0, 0, 0), Vector(8, 0, 0))
        L2 = Draft.makeLine(Vector(8, 0, 0), Vector(8, 8, 0))
        App.ActiveDocument.recompute()
        import DraftFillet
        obj = DraftFillet.makeFillet([L1, L2], 4)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_circle(self):
        """Create a circle."""
        func = "Draft Circle"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeCircle(3)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_arc(self):
        """Create a circular arc."""
        func = "Draft Arc"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeCircle(2, startangle=0, endangle=90)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_arc_3points(self):
        """Create a circular arc from three points."""
        func = "Draft Arc 3Points"
        _msg("  Test '{0}'".format(func))
        Draft.make_arc_3points = _fake_func
        obj = Draft.make_arc_3points(Vector(5, 0, 0),
                                     Vector(4, 3, 0),
                                     Vector(0, 5, 0))
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_ellipse(self):
        """Create an ellipse."""
        func = "Draft Ellipse"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeEllipse(5, 3)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_polygon(self):
        """Create a regular polygon."""
        func = "Draft Polygon"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makePolygon(5, 5)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_rectangle(self):
        """Create a rectangle."""
        func = "Draft Rectangle"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeRectangle(4, 2)
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_text(self):
        """Create a text object."""
        func = "Draft Text"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeText("Testing Draft")
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_dimension_linear(self):
        """Create a linear dimension."""
        func = "Draft Dimension"
        _msg("  Test '{0}'".format(func))
        obj = Draft.makeDimension(Vector(0, 0, 0),
                                  Vector(2, 0, 0),
                                  Vector(1, -1, 0))
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_dimension_radial(self):
        """Create a radial dimension. NOT IMPLEMENTED CURRENTLY."""
        func = "Draft Dimension Radial"
        _msg("  Test '{0}'".format(func))
        Draft.make_dimension_radial = _fake_func
        obj = Draft.make_dimension_radial(Vector(5, 0, 0),
                                          Vector(4, 3, 0),
                                          Vector(0, 5, 0))
        self.assertTrue(obj, "'{0}' failed".format(func))

    def test_bspline(self):
        """Create a BSpline of three points."""
        App.Console.PrintLog('Checking Draft BSpline...\n')
        Draft.makeBSpline([Vector(0, 0, 0),
                           Vector(2, 0, 0),
                           Vector(2, 2, 0)])
        self.assertTrue(App.ActiveDocument.getObject("BSpline"),
                        "Draft BSpline failed")

    def test_point(self):
        """Create a point."""
        App.Console.PrintLog('Checking Draft Point...\n')
        Draft.makePoint(5, 3, 2)
        self.assertTrue(App.ActiveDocument.getObject("Point"),
                        "Draft Point failed")

    def test_shapestring(self):
        """Create a ShapeString. NOT IMPLEMENTED CURRENTLY."""
        App.Console.PrintLog('Checking Draft ShapeString...\n')
        _msg("This test doesn't do anything at the moment. "
             "In order to test this, a font file is needed.")
        # Draft.makeShapeString("Text", FontFile="")
        # self.assertTrue(App.ActiveDocument.getObject("ShapeString"),
        #                 "Draft ShapeString failed")
        self.assertTrue(True,
                        "Draft ShapeString failed")

    def test_facebinder(self):
        """Create a Facebinder. NOT IMPLEMENTED CURRENTLY."""
        App.Console.PrintLog('Checking Draft FaceBinder...\n')
        _msg("This test doesn't do anything at the moment. "
             "In order to test this, a selection is needed.")
        # Draft.makeFacebinder(selectionset)
        # self.assertTrue(App.ActiveDocument.getObject("Facebinder"),
        #                 "Draft FaceBinder failed")
        self.assertTrue(True,
                        "Draft FaceBinder failed")

    def test_cubicbezcurve(self):
        """Create a cubic bezier curve of four points."""
        App.Console.PrintLog('Checking Draft CubicBezCurve...\n')
        Draft.makeBezCurve([Vector(0, 0, 0),
                            Vector(2, 2, 0),
                            Vector(5, 3, 0),
                            Vector(9, 0, 0)], Degree=3)
        self.assertTrue(App.ActiveDocument.getObject("BezCurve"),
                        "Draft CubicBezCurve failed")

    def test_bezcurve(self):
        """Create a bezier curve of six points, degree five."""
        App.Console.PrintLog('Checking Draft BezCurve...\n')
        Draft.makeBezCurve([Vector(0, 0, 0),
                            Vector(2, 2, 0),
                            Vector(5, 3, 0),
                            Vector(9, 0, 0),
                            Vector(12, 5, 0),
                            Vector(12, 8, 0)])
        self.assertTrue(App.ActiveDocument.getObject("BezCurve"),
                        "Draft BezCurve failed")
        App.Console.PrintLog('Currently no test!\n')
        self.assertTrue(True,
                        "Draft BezCurve failed")

    def test_label(self):
        """Create a label."""
        App.Console.PrintLog('Checking Draft Label...\n')
        place = App.Placement(Vector(50, 50, 0), App.Rotation())
        Draft.makeLabel(targetpoint=Vector(0, 0, 0),
                        distance=-25,
                        placement=place)
        self.assertTrue(App.ActiveDocument.getObject("dLabel"),
                        "Draft Label failed")

    def tearDown(self):
        # clearance, is executed after every test
        App.closeDocument(self.doc_name)


class DraftModification(unittest.TestCase):
    """Test Draft modification tools."""

    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftTest":
                App.newDocument("DraftTest")
        else:
            App.newDocument("DraftTest")
        App.setActiveDocument("DraftTest")

    def testMove(self):
        """Create a line and move it."""
        App.Console.PrintLog('Checking Draft Move...\n')
        line = Draft.makeLine(Vector(0, 0, 0), Vector(-2, 0, 0))
        Draft.move(line, Vector(2, 0, 0))
        self.assertTrue(line.Start == Vector(2, 0, 0),
                        "Draft Move failed")

    def testCopy(self):
        """Create a line, then copy and move it."""
        App.Console.PrintLog('Checking Draft Move with copy...\n')
        line = Draft.makeLine(Vector(0, 0, 0), Vector(2, 0, 0))
        line2 = Draft.move(line, Vector(2, 0, 0), copy=True)
        self.assertTrue(line2, "Draft Move with copy failed")

    def testRotate(self):
        """Create a line, then rotate it."""
        App.Console.PrintLog('Checking Draft Rotate...\n')
        line = Draft.makeLine(Vector(2, 0, 0), Vector(4, 0, 0))
        App.ActiveDocument.recompute()
        Draft.rotate(line, 90)
        self.assertTrue(line.Start.isEqual(Vector(0, 2, 0), 1e-12),
                        "Draft Rotate failed")

    def testOffset(self):
        """Create a rectangle, then produce an offset copy."""
        App.Console.PrintLog('Checking Draft Offset...\n')
        r = Draft.makeRectangle(4, 2)
        App.ActiveDocument.recompute()
        r2 = Draft.offset(r, Vector(-1, -1, 0), copy=True)
        self.assertTrue(r2, "Draft Offset failed")

    def test_trim(self):
        """Trim a line. NOT IMPLEMENTED."""
        pass

    def test_extend(self):
        """Extend a line. NOT IMPLEMENTED."""
        pass

    def test_join(self):
        """Join two lines. NOT IMPLEMENTED."""
        pass

    def test_split(self):
        """Split a polyline. NOT IMPLEMENTED."""
        pass

    def test_upgrade(self):
        """Upgrade series of edges. NOT IMPLEMENTED."""
        pass

    def test_downgrade(self):
        """Downgrade a face. NOT IMPLEMENTED."""
        pass

    def test_wire_to_Bspline(self):
        """Convert a polyline to BSpline. NOT IMPLEMENTED."""
        pass

    def test_shape_2D_view(self):
        """Create a 2D projection. NOT IMPLEMENTED."""
        pass

    def test_draft_to_sketch(self):
        """Convert a Draft object to a Sketch. NOT IMPLEMENTED."""
        pass

    def test_sketch_to_draft(self):
        """Convert a Sketch to Draft object. NOT IMPLEMENTED."""
        pass

    def test_rectangular_array(self):
        """Create a rectangular array. NOT IMPLEMENTED."""
        pass

    def test_polar_array(self):
        """Create a polar array. NOT IMPLEMENTED."""
        pass

    def test_path_array(self):
        """Create a path array. NOT IMPLEMENTED."""
        pass

    def test_point_array(self):
        """Create a point array. NOT IMPLEMENTED."""
        pass

    def testCloneOfPart(self):
        """Create a clone of a Part.Box."""

    def test_text(self):
        """Create a text object."""
        operation = "Draft Text"
        _msg("  Test '{}'".format(operation))
        text = "Testing testing"
        _msg("  text='{}'".format(text))
        obj = Draft.makeText(text)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_dimension_linear(self):
        """Create a linear dimension."""
        operation = "Draft Dimension"
        _msg("  Test '{}'".format(operation))
        _msg("  Occasionaly crashes")
        a = Vector(0, 0, 0)
        b = Vector(9, 0, 0)
        c = Vector(4, -1, 0)
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={}".format(c))
        obj = Draft.makeDimension(a, b, c)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_dimension_radial(self):
        """Create a radial dimension. NOT IMPLEMENTED CURRENTLY."""
        operation = "Draft Dimension Radial"
        _msg("  Test '{}'".format(operation))
        a = Vector(5, 0, 0)
        b = Vector(4, 3, 0)
        c = Vector(0, 5, 0)
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={}".format(c))
        Draft.make_dimension_radial = _fake_function
        obj = Draft.make_dimension_radial(a, b, c)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_bspline(self):
        """Create a BSpline of three points."""
        operation = "Draft BSpline"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 0, 0)
        c = Vector(2, 2, 0)
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={}".format(c))
        obj = Draft.makeBSpline([a, b, c])
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_point(self):
        """Create a point."""
        operation = "Draft Point"
        _msg("  Test '{}'".format(operation))
        p = Vector(5, 3, 2)
        _msg("  p.x={0}, p.y={1}, p.z={2}".format(p.x, p.y, p.z))
        obj = Draft.makePoint(p.x, p.y, p.z)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_shapestring(self):
        """Create a ShapeString. NOT IMPLEMENTED CURRENTLY."""
        operation = "Draft ShapeString"
        _msg("  Test '{}'".format(operation))
        _msg("  In order to test this, a font file is needed.")
        text = "Testing Shapestring "
        font = None  # TODO: get a font file here
        _msg("  text='{0}', font='{1}'".format(text, font))
        Draft.makeShapeString = _fake_function
        obj = Draft.makeShapeString("Text", font)
        # Draft.makeShapeString("Text", FontFile="")
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_facebinder(self):
        """Create a box, and then a facebinder from its faces."""
        operation = "Draft Facebinder"
        _msg("  Test '{}'".format(operation))
        _msg("  In order to test this, a selection is needed")
        _msg("  or an App::PropertyLinkSubList")

        _msg("  Box")
        box = App.ActiveDocument.addObject("Part::Box")
        App.ActiveDocument.recompute()
        # The facebinder function accepts a Gui selection set,
        # or a 'PropertyLinkSubList'

        # Gui selection set only works when the graphical interface is up
        # Gui.Selection.addSelection(box, ('Face1', 'Face6'))
        # selection_set = Gui.Selection.getSelectionEx()
        # elements = selection_set[0].SubElementNames

        # PropertyLinkSubList
        selection_set = [(box, ("Face1", "Face6"))]
        elements = selection_set[0][1]
        _msg("  object='{0}' ({1})".format(box.Shape.ShapeType, box.TypeId))
        _msg("  sub-elements={}".format(elements))
        obj = Draft.makeFacebinder(selection_set)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_cubicbezcurve(self):
        """Create a cubic bezier curve of four points."""
        operation = "Draft CubBezCurve"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(5, 3, 0)
        d = Vector(9, 0, 0)
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, d={1}".format(c, d))
        obj = Draft.makeBezCurve([a, b, c, d], degree=3)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_bezcurve(self):
        """Create a bezier curve of six points, degree five."""
        operation = "Draft BezCurve"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(5, 3, 0)
        d = Vector(9, 0, 0)
        e = Vector(12, 5, 0)
        f = Vector(12, 8, 0)
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, d={1}".format(c, d))
        _msg("  e={0}, f={1}".format(e, f))
        obj = Draft.makeBezCurve([a, b, c, d, e, f])
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_label(self):
        """Create a label."""
        operation = "Draft Label"
        _msg("  Test '{}'".format(operation))
        _msg("  Occasionaly crashes")
        target_point = Vector(0, 0, 0)
        distance = -25
        placement = App.Placement(Vector(50, 50, 0), App.Rotation())
        _msg("  target_point={0}, "
             "distance={1}".format(target_point, distance))
        _msg("  placement={}".format(placement))
        obj = Draft.makeLabel(targetpoint=target_point,
                              distance=distance,
                              placement=placement)
        App.ActiveDocument.recompute()
        self.assertTrue(obj, "'{}' failed".format(operation))

    def tearDown(self):
        """Finish the test.

        This is executed after each test, so we close the document.
        """
        App.closeDocument(self.doc_name)


class DraftModification(unittest.TestCase):
    """Test Draft modification tools."""

    def setUp(self):
        """Set up a new document to hold the tests.

        This is executed before every test, so we create a document
        to hold the objects.
        """
        _draw_header()
        self.doc_name = self.__class__.__name__
        if App.ActiveDocument:
            if App.ActiveDocument.Name != self.doc_name:
                App.newDocument(self.doc_name)
        else:
            App.newDocument(self.doc_name)
        App.setActiveDocument(self.doc_name)
        self.doc = App.ActiveDocument
        _msg("  Temporary document '{}'".format(self.doc_name))

    def test_move(self):
        """Create a line and move it."""
        operation = "Draft Move"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 2, 0)
        b = Vector(2, 2, 0)
        _msg("  Line")
        _msg("  a={0}, b={1}".format(a, b))
        obj = Draft.makeLine(a, b)

        c = Vector(3, 1, 0)
        _msg("  Translation vector")
        _msg("  c={}".format(c))
        Draft.move(obj, c)
        self.assertTrue(obj.Start == Vector(3, 3, 0),
                        "'{}' failed".format(operation))

    def test_copy(self):
        """Create a line, then copy and move it."""
        operation = "Draft Move with copy"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 3, 0)
        b = Vector(2, 3, 0)
        _msg("  Line")
        _msg("  a={0}, b={1}".format(a, b))
        line = Draft.makeLine(a, b)

        c = Vector(2, 2, 0)
        _msg("  Translation vector (copy)")
        _msg("  c={}".format(c))
        obj = Draft.move(line, c, copy=True)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_rotate(self):
        """Create a line, then rotate it."""
        operation = "Draft Rotate"
        _msg("  Test '{}'".format(operation))
        a = Vector(1, 1, 0)
        b = Vector(3, 1, 0)
        _msg("  Line")
        _msg("  a={0}, b={1}".format(a, b))
        obj = Draft.makeLine(a, b)
        App.ActiveDocument.recompute()

        c = Vector(-1, 1, 0)
        rot = 90
        _msg("  Rotation")
        _msg("  angle={} degrees".format(rot))
        Draft.rotate(obj, rot)
        self.assertTrue(obj.Start.isEqual(c, 1e-12),
                        "'{}' failed".format(operation))

    def test_offset(self):
        """Create a rectangle, then produce an offset copy."""
        operation = "Draft Offset"
        _msg("  Test '{}'".format(operation))
        length = 4
        width = 2
        _msg("  Rectangle")
        _msg("  length={0}, width={1}".format(length, width))
        rect = Draft.makeRectangle(length, width)
        App.ActiveDocument.recompute()

        offset = Vector(-1, -1, 0)
        _msg("  Offset")
        _msg("  vector={}".format(offset))
        obj = Draft.offset(rect, offset, copy=True)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_trim(self):
        """Trim a line. NOT IMPLEMENTED."""
        operation = "Draft Trimex trim"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(3, 3, 0)

        _msg("  Line")
        _msg("  a={0}, b={1}".format(a, b))
        line = Draft.makeLine(a, b)

        c = Vector(2, 2, 0)
        d = Vector(4, 2, 0)
        _msg("  Line 2")
        _msg("  c={0}, d={1}".format(c, d))
        line2 = Draft.makeLine(c, d)
        App.ActiveDocument.recompute()

        Draft.trim_objects = _fake_function
        obj = Draft.trim_objects(line, line2)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_extend(self):
        """Extend a line. NOT IMPLEMENTED."""
        operation = "Draft Trimex extend"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(1, 1, 0)
        _msg("  Line")
        _msg("  a={0}, b={1}".format(a, b))
        line = Draft.makeLine(a, b)

        c = Vector(2, 2, 0)
        d = Vector(4, 2, 0)
        _msg("  Line 2")
        _msg("  c={0}, d={1}".format(c, d))
        line2 = Draft.makeLine(c, d)
        App.ActiveDocument.recompute()

        Draft.extrude = _fake_function
        obj = Draft.extrude(line, line2)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_join(self):
        """Join two lines into a single Draft Wire."""
        operation = "Draft Join"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        _msg("  Line 1")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  Line 2")
        _msg("  b={0}, c={1}".format(b, c))
        line_1 = Draft.makeLine(a, b)
        line_2 = Draft.makeLine(b, c)

        # obj = Draft.joinWires([line_1, line_2])  # Multiple wires
        obj = Draft.joinTwoWires(line_1, line_2)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_split(self):
        """Split a Draft Wire into two Draft Wires."""
        operation = "Draft_Split"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        d = Vector(6, 4, 0)
        _msg("  Wire")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, d={1}".format(c, d))
        wire = Draft.makeWire([a, b, c, d])

        index = 1
        _msg("  Split at")
        _msg("  p={0}, index={1}".format(b, index))
        obj = Draft.split(wire, b, index)
        # TODO: split needs to be modified so that it returns True or False.
        # Then checking for Wire001 is not needed
        if App.ActiveDocument.Wire001:
            obj = True
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_upgrade(self):
        """Upgrade two Draft Lines into a closed Draft Wire."""
        operation = "Draft Upgrade"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        _msg("  Line 1")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  Line 2")
        _msg("  b={0}, c={1}".format(b, c))
        line_1 = Draft.makeLine(a, b)
        line_2 = Draft.makeLine(b, c)
        App.ActiveDocument.recompute()

        obj = Draft.upgrade([line_1, line_2], delete=True)
        App.ActiveDocument.recompute()
        s = obj[0][0]
        _msg("  1: Result '{0}' ({1})".format(s.Shape.ShapeType, s.TypeId))
        self.assertTrue(bool(obj[0]), "'{}' failed".format(operation))

        obj2 = Draft.upgrade(obj[0], delete=True)
        App.ActiveDocument.recompute()
        s2 = obj2[0][0]
        _msg("  2: Result '{0}' ({1})".format(s2.Shape.ShapeType,
                                              s2.TypeId))
        self.assertTrue(bool(obj2[0]), "'{}' failed".format(operation))

        obj3 = Draft.upgrade(obj2[0], delete=True)
        App.ActiveDocument.recompute()
        s3 = obj3[0][0]
        _msg("  3: Result '{0}' ({1})".format(s3.Shape.ShapeType, s3.TypeId))
        self.assertTrue(bool(obj3[0]), "'{}' failed".format(operation))

        obj4 = Draft.upgrade(obj3[0], delete=True)
        App.ActiveDocument.recompute()
        wire = App.ActiveDocument.Wire
        _msg("  4: Result '{0}' ({1})".format(wire.Proxy.Type, wire.TypeId))
        _msg("  The last object cannot be upgraded further")
        self.assertFalse(bool(obj4[0]), "'{}' failed".format(operation))

    def test_downgrade(self):
        """Downgrade a closed Draft Wire into three simple Part Edges."""
        operation = "Draft Downgrade"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        _msg("  Closed wire")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, a={1}".format(c, a))
        wire = Draft.makeWire([a, b, c, a])
        App.ActiveDocument.recompute()

        obj = Draft.downgrade(wire, delete=True)
        App.ActiveDocument.recompute()
        s = obj[0][0]
        _msg("  1: Result '{0}' ({1})".format(s.Shape.ShapeType, s.TypeId))
        self.assertTrue(bool(obj[0]), "'{}' failed".format(operation))

        obj2 = Draft.downgrade(obj[0], delete=True)
        App.ActiveDocument.recompute()
        s2 = obj2[0][0]
        _msg("  2: Result '{0}' ({1})".format(s2.Shape.ShapeType, s2.TypeId))
        self.assertTrue(bool(obj2[0]), "'{}' failed".format(operation))

        obj3 = Draft.downgrade(obj2[0], delete=True)
        App.ActiveDocument.recompute()
        s3 = obj3[0][0]
        _msg("  3: Result 3 x '{0}' ({1})".format(s3.Shape.ShapeType,
                                                  s3.TypeId))
        self.assertTrue(len(obj3[0]) == 3, "'{}' failed".format(operation))

        obj4 = Draft.downgrade(obj3[0], delete=True)
        App.ActiveDocument.recompute()
        s4 = obj4[0]
        _msg("  4: Result '{}'".format(s4))
        _msg("  The last objects cannot be downgraded further")
        self.assertFalse(bool(obj4[0]), "'{}' failed".format(operation))

    def test_wire_to_bspline(self):
        """Convert a polyline to BSpline and back."""
        operation = "Draft WireToBSpline"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        _msg("  Wire")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={}".format(c))
        wire = Draft.makeWire([a, b, c])

        obj = Draft.makeBSpline(wire.Points)
        App.ActiveDocument.recompute()
        _msg("  1: Result '{0}' ({1})".format(obj.Proxy.Type, obj.TypeId))
        self.assertTrue(obj, "'{}' failed".format(operation))

        obj2 = Draft.makeWire(obj.Points)
        _msg("  2: Result '{0}' ({1})".format(obj2.Proxy.Type, obj2.TypeId))
        self.assertTrue(obj2, "'{}' failed".format(operation))

    def test_shape_2d_view(self):
        """Create a prism and then a 2D projection of it."""
        operation = "Draft Shape2DView"
        _msg("  Test '{}'".format(operation))
        prism = App.ActiveDocument.addObject("Part::Prism")
        prism.Polygon = 5
        # Rotate the prism 45 degrees around the Y axis
        prism.Placement.Rotation.Axis = Vector(0, 1, 0)
        prism.Placement.Rotation.Angle = 45 * (3.14159/180)
        _msg("  Prism")
        _msg("  n_sides={}".format(prism.Polygon))
        _msg("  placement={}".format(prism.Placement))

        direction = Vector(0, 0, 1)
        _msg("  Projection 2D view")
        _msg("  direction={}".format(direction))
        obj = Draft.makeShape2DView(prism, direction)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_draft_to_sketch(self):
        """Convert a Draft object to a Sketch and back."""
        operation = "Draft Draft2Sketch"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        _msg("  Wire")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={}".format(c))
        wire = Draft.makeWire([a, b, c])
        App.ActiveDocument.recompute()

        obj = Draft.makeSketch(wire, autoconstraints=True)
        App.ActiveDocument.recompute()
        _msg("  1: Result '{0}' ({1})".format(obj.Shape.ShapeType,
                                              obj.TypeId))
        self.assertTrue(obj, "'{}' failed".format(operation))

        obj2 = Draft.draftify(obj, delete=False)
        App.ActiveDocument.recompute()
        _msg("  2: Result '{0}' ({1})".format(obj2.Proxy.Type,
                                              obj2.TypeId))
        self.assertTrue(obj2, "'{}' failed".format(operation))

    def test_rectangular_array(self):
        """Create a rectangle, and a rectangular array."""
        operation = "Draft Array"
        _msg("  Test '{}'".format(operation))
        length = 4
        width = 2
        _msg("  Rectangle")
        _msg("  length={0}, width={1}".format(length, width))
        rect = Draft.makeRectangle(length, width)
        App.ActiveDocument.recompute()

        dir_x = Vector(5, 0, 0)
        dir_y = Vector(0, 4, 0)
        number_x = 3
        number_y = 4
        _msg("  Array")
        _msg("  direction_x={}".format(dir_x))
        _msg("  direction_y={}".format(dir_y))
        _msg("  number_x={0}, number_y={1}".format(number_x, number_y))
        obj = Draft.makeArray(rect,
                              dir_x, dir_y,
                              number_x, number_y)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_polar_array(self):
        """Create a rectangle, and a polar array."""
        operation = "Draft PolarArray"
        _msg("  Test '{}'".format(operation))
        length = 4
        width = 2
        _msg("  Rectangle")
        _msg("  length={0}, width={1}".format(length, width))
        rect = Draft.makeRectangle(length, width)
        App.ActiveDocument.recompute()

        center = Vector(-4, 0, 0)
        angle = 180
        number = 5
        _msg("  Array")
        _msg("  center={}".format(center))
        _msg("  polar_angle={0}, number={1}".format(angle, number))
        obj = Draft.makeArray(rect,
                              center, angle, number)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_circular_array(self):
        """Create a rectangle, and a circular array."""
        operation = "Draft CircularArray"
        _msg("  Test '{}'".format(operation))
        length = 4
        width = 2
        _msg("  Rectangle")
        _msg("  length={0}, width={1}".format(length, width))
        rect = Draft.makeRectangle(length, width)
        App.ActiveDocument.recompute()

        rad_distance = 10
        tan_distance = 8
        axis = Vector(0, 0, 1)
        center = Vector(0, 0, 0)
        number = 3
        symmetry = 1
        _msg("  Array")
        _msg("  radial_distance={0}, "
             "tangential_distance={1}".format(rad_distance, tan_distance))
        _msg("  axis={}".format(axis))
        _msg("  center={}".format(center))
        _msg("  number={0}, symmetry={1}".format(number, symmetry))
        obj = Draft.makeArray(rect,
                              rad_distance, tan_distance,
                              axis, center,
                              number, symmetry)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_path_array(self):
        """Create a wire, a polygon, and a path array."""
        operation = "Draft PathArray"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        d = Vector(8, 4, 0)
        _msg("  Wire")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, d={1}".format(c, d))
        wire = Draft.makeWire([a, b, c, d])

        n_faces = 3
        radius = 1
        _msg("  Polygon")
        _msg("  n_faces={0}, radius={1}".format(n_faces, radius))
        poly = Draft.makePolygon(n_faces, radius)

        number = 4
        translation = Vector(0, 1, 0)
        align = False
        _msg("  Path Array")
        _msg("  number={}, translation={}".format(number, translation))
        _msg("  align={}".format(align))
        obj = Draft.makePathArray(poly, wire, number, translation, align)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_point_array(self):
        """Create a polygon, various point, and a point array."""
        operation = "Draft PointArray"
        _msg("  Test '{}'".format(operation))
        a = Vector(0, 0, 0)
        b = Vector(2, 2, 0)
        c = Vector(2, 4, 0)
        d = Vector(8, 4, 0)
        _msg("  Points")
        _msg("  a={0}, b={1}".format(a, b))
        _msg("  c={0}, d={1}".format(c, d))
        points = [Draft.makePoint(a),
                  Draft.makePoint(b),
                  Draft.makePoint(c),
                  Draft.makePoint(d)]

        _msg("  Upgrade")
        add, delete = Draft.upgrade(points)
        compound = add[0]

        n_faces = 3
        radius = 1
        _msg("  Polygon")
        _msg("  n_faces={0}, radius={1}".format(n_faces, radius))
        poly = Draft.makePolygon(n_faces, radius)

        _msg("  Point Array")
        obj = Draft.makePointArray(poly, compound)
        self.assertTrue(obj, "'{}' failed".format(operation))

    def test_clone(self):
        """Create a box, then create a clone of it.

        Test for a bug introduced by changes in attachment code.
        """
        box = App.ActiveDocument.addObject("Part::Box", "Box")
        clone = Draft.clone(box)
        self.assertTrue(clone.hasExtension("Part::AttachExtension"))

    def test_draft_to_drawing(self):
        """Create a draft projection in a Drawing page. NOT IMPLEMENTED."""
        pass

    def test_mirror(self):
        """Create a mirrored shape. NOT IMPLEMENTED."""
        pass

    def test_stretch(self):
        """Stretch a line. NOT IMPLEMENTED."""
        pass

    def tearDown(self):
        App.closeDocument("DraftTest")


class DraftSVG(unittest.TestCase):
    """Test reading and writing of SVGs with Draft."""
    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftSVGTest":
                App.newDocument("DraftSVGTest")
        else:
            App.newDocument("DraftSVGTest")
        App.setActiveDocument("DraftSVGTest")

    def test_read_SVG(self):
        """Read an SVG."""
        _msg("Test currently not implemented")
        pass

    def test_export_SVG(self):
        """Export an SVG."""
        _msg("Test currently not implemented")
        pass


class DraftDXF(unittest.TestCase):
    """Test reading and writing of DXF with Draft."""

    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftDXFTest":
                App.newDocument("DraftDXFTest")
        else:
            App.newDocument("DraftDXFTest")
        App.setActiveDocument("DraftDXFTest")

    def test_read_DXF(self):
        """Read a DXF."""
        _msg("Test currently not implemented")
        pass

    def test_export_DXF(self):
        """Export a DXF."""
        _msg("Test currently not implemented")
        pass


class DraftDWG(unittest.TestCase):
    """Test reading and writing of DWG with Draft."""

    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftDXFTest":
                App.newDocument("DraftDXFTest")
        else:
            App.newDocument("DraftDXFTest")
        App.setActiveDocument("DraftDXFTest")

    def test_read_DXF(self):
        """Read a DXF."""
        _msg("Test currently not implemented")
        pass

    def test_export_DXF(self):
        """Export a DXF."""
        _msg("Test currently not implemented")
        pass


class DraftOCA(unittest.TestCase):
    """Test reading and writing of OCA with Draft."""

    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftDXFTest":
                App.newDocument("DraftDXFTest")
        else:
            App.newDocument("DraftDXFTest")
        App.setActiveDocument("DraftDXFTest")

    def test_read_DXF(self):
        """Read a DXF."""
        _msg("Test currently not implemented")
        pass

    def test_export_DXF(self):
        """Export a DXF."""
        _msg("Test currently not implemented")
        pass


class DraftAirfoilDAT(unittest.TestCase):
    """Test reading and writing of AirfoilDAT with Draft."""

    def setUp(self):
        """Set up a new document to hold the tests"""
        if App.ActiveDocument:
            if App.ActiveDocument.Name != "DraftDXFTest":
                App.newDocument("DraftDXFTest")
        else:
            App.newDocument("DraftDXFTest")
        App.setActiveDocument("DraftDXFTest")

    def test_read_DXF(self):
        """Read a DXF."""
        _msg("Test currently not implemented")
        pass

    def test_export_DXF(self):
        """Export a DXF."""
        _msg("Test currently not implemented")
        pass
