---
size: big
modified_date: 2026-04-17
---

Create a webapp that allows users to create their own CVs

Goal: Allow via the use of forms, for users to leave the website with a CV in pdf form but also the yaml version of their data. In this sense, the website should not be storing any user data (outside the duration of a session of course)


- First version with document as web component loading individually from the whole page and checkboxes to select sections of the document to be loaded / shown
- Create control component
	- functionality
		- change the overall design
		- show available sections
		- change their order
		- change their design
		- list available data to show
		- Select from the list of available data to 
			- show
			- edit
	- Challenges
		- naming data can be a challenge we could ask users to name them for us
- Create editing components
	- This could be either a dialog or a series of pages
	- Each page should collect data for a certain section
		- It should show a (live) preview of the section that is being created using the input data
		- It could also show a live preview of the yaml corresponding to the input data
	- Form component
		- Stateless, gets the form elements from the data schema of the current section
	- Yaml component
		- Shows in real time the yaml markup as it is being created
			- Use bound variables, keep it client-side
	- Document preview component
		- Shows the document as it is being created
			- live preview would require to create a version with bound variable based on the data of the section that is being edited (not impossible)
			- alternatively we could 


# Technical
Use [[Flask.py]], [[Alpine.js]] for interactivity and an [[htmx]]-style solution to get data from the server without having to reload the page. We want to create a Server driven website instead of any client-heavy frameworks.