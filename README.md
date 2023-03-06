# Trends in Microscopy 2023
### Workshop 44
### High throughput data analysis and management with Cellprofiler and OMERO

Workshop provider:
Thomas Zobel & Sarah Weischer <br>
Münster Imaging Network,<br> Cells in Motion Interfaculty Centre,<br> University of Münster

<br>
### Abstract
<br>
The image data management system OMERO allows to organize and store data according to the FAIR principles. To perform image analysis, however, the image data often is downloaded to the local analysis station causing unnecessary duplication of data. Consequently, upload of analysis results, including reporting on analysis metadata (e.g. used analysis pipelines) has to be performed manually.

<br>
<br>
![Graph_Workflow](https://user-images.githubusercontent.com/96130744/223094716-b9b478a3-ae17-467e-9e53-c7540ab5db82.png)

<br>
<br>
During this workshop we will present fully integrated data analysis solutions employing OMERO and commonly applied image analysis tools (e.g., CellProfiler, Fiji) using existing python interfaces (OMERO Python language bindings, ezOmero, Cellprofiler Python API). 
<br>

#### Workshop topics: <br>
1 Data import to OMERO and preparation for analysis 

2 Automated data download/injection into analysis pipeline

3 Automated data analysis using image analysis pipelines (e.g., Cellprofiler)

4 Upload of the resulting images (including tags and metadata) and measurement results (omero.tables)

5 Explorative data analysis using omero.parade/omero.parade-crossfilter
<br>
<br>
During the hands-on session workshop participants will learn to analyze provided example datasets, execute the full workflow and perform easy adjustments of the pipeline (e.g. generation of new project/datasets, selection of image channels or ROIs for analysis, key:value pair annotation, file tagging, changes in file format), followed by explorative data analysis using omero.parade.


### Analysed Image Data:
The data used for this workshop has been published and is publicly available in the Image Data Ressource (IDR). <br>
https://idr.openmicroscopy.org/webclient/?show=screen-1651

##### Publication Title
RNAi screens for Rho GTPase regulators of cell shape and YAP/TAZ localisation in triple negative breast cancer.

##### Screen Description
Human RhoGEF/RhoGAP siGenome siRNA screen on highly metastatic triple negative breast cancer cell line LM2

##### Authors
Pascual-Vargas P, Cooper S, Sero J, Bousgouni V, Arias-Garcia M, Bakal C <br>

DOI: 10.1038/sdata.2017.18 https://doi.org/10.1038/sdata.2017.18


### In this repo you will find:

Upload:
- JN1, Omero
- JN2 (from disk, back-up)
- Environment installation
- Presentation
- 
