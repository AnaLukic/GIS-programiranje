from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterDestination
import processing


class ForestFiresSusceptibilityIndexRc(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('a', 'A', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('dr', 'Dr', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('ds', 'Ds', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('s', 'S', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('vt', 'Vt', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('RcIndexSusceptibilityClasses', 'RC INDEX - Susceptibility classes', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('RcIndex', 'RC INDEX', createByDefault=True, defaultValue=''))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(7, model_feedback)
        results = {}
        outputs = {}

        # Rasterize (vector to raster) - Ds
        alg_params = {
            'BURN': 0,
            'DATA_TYPE': 5,
            'EXTENT': parameters['ds'],
            'FIELD': 'Vrednost',
            'HEIGHT': 25,
            'INIT': None,
            'INPUT': parameters['ds'],
            'INVERT': False,
            'NODATA': -9999,
            'OPTIONS': '',
            'UNITS': 1,
            'WIDTH': 25,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeVectorToRasterDs'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Reclassify by table - S
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': parameters['s'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [0,5,1,5,10,2,10,25,3,25,35,4,35,100,5],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyByTableS'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster) - Dr
        alg_params = {
            'BURN': 0,
            'DATA_TYPE': 5,
            'EXTENT': parameters['dr'],
            'FIELD': 'Vrednost',
            'HEIGHT': 25,
            'INIT': None,
            'INPUT': parameters['dr'],
            'INVERT': False,
            'NODATA': -9999,
            'OPTIONS': '',
            'UNITS': 1,
            'WIDTH': 25,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeVectorToRasterDr'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Rasterize (vector to raster) - Vt
        alg_params = {
            'BURN': 0,
            'DATA_TYPE': 5,
            'EXTENT': parameters['vt'],
            'FIELD': 'Vrednost',
            'HEIGHT': 25,
            'INIT': None,
            'INPUT': parameters['vt'],
            'INVERT': False,
            'NODATA': -9999,
            'OPTIONS': '',
            'UNITS': 1,
            'WIDTH': 25,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeVectorToRasterVt'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Reclassify by table - A
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': parameters['a'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [0,0.00000001,2,0.00000001,22.5,1,22.5,67.5,2,67.5,112.5,3,112.5,157.5,4,157.5,202.5,5,202.5,247.5,4,247.5,292.5,3,292.5,337.5,2,337.5,400,1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyByTableA'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Raster calculator
        alg_params = {
            'FORMULA': '7*a+5*(b+c)+3*(d+e)',
            'GRIDS': outputs['RasterizeVectorToRasterVt']['OUTPUT'],
            'RESAMPLING': 0,
            'TYPE': 7,
            'USE_NODATA': False,
            'XGRIDS': [outputs['RasterizeVectorToRasterDr']['OUTPUT'],outputs['RasterizeVectorToRasterDs']['OUTPUT'],outputs['ReclassifyByTableA']['OUTPUT'],outputs['ReclassifyByTableS']['OUTPUT']],
            'RESULT': parameters['RcIndex']
        }
        outputs['RasterCalculator'] = processing.run('saga:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['RcIndex'] = outputs['RasterCalculator']['RESULT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Reclassify by table
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['RasterCalculator']['RESULT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [0,60,1,60,75,2,75,90,3,90,1000,4],
            'OUTPUT': parameters['RcIndexSusceptibilityClasses']
        }
        outputs['ReclassifyByTable'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['RcIndexSusceptibilityClasses'] = outputs['ReclassifyByTable']['OUTPUT']
        return results

    def name(self):
        return 'Forest Fires Susceptibility Index - RC'

    def displayName(self):
        return 'Forest Fires Susceptibility Index - RC'

    def group(self):
        return 'GIS programiranje'

    def groupId(self):
        return 'GIS programiranje'

    def createInstance(self):
        return ForestFiresSusceptibilityIndexRc()
