from typing import Any, Dict, List, Optional
import sys
import traceback
import logging
import httpx
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("knowledge_vault")

# Create a FastAPI app
app = FastAPI(title="Knowledge Vault MCP API")

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stderr)

print("Starting knowledge_vault MCP server...", file=sys.stderr)

# API configuration
# NEXT_PUBLIC_API_HOST = "http://127.0.0.1:5000"
NEXT_PUBLIC_API_HOST = "https://api.youfondu.com"

USER_AGENT = "personal-vault-app/1.0"

try:
    error_log = open("/tmp/error_log.txt", "a")
except OSError:
    # Fall back to using stderr for logging when file can't be created
    import sys
    error_log = sys.stderr

async def make_fondu_api_request(url: str, method: str = "GET", json_data: dict = None) -> dict[str, Any] | None:
    """Make a request to the API with proper error handling."""
    logging.debug(f"Making {method} request to: {url}")
    headers = {
        # "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    logging.debug(f"Using headers: {headers}")
    async with httpx.AsyncClient() as client:
        try:
            logging.debug(f"Sending HTTP {method} request...")
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=30.0)
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return None
                
            logging.debug(f"Received HTTP status code: {response.status_code}")
            response.raise_for_status()
            logging.debug("Successfully parsed JSON response")
            return response.json()
        except Exception as e:
            logging.error(f"Error in API request: {type(e).__name__}: {str(e)}")
            error_log.write(f"ERROR: {str(e)}\n")
            error_log.flush()
            return None


        
@mcp.tool()
async def gather_relevant_user_knowledge(
    query: str,
    # user_id: str,
    keywords: str = "",
    top_k: int = 10
) -> str:
    """Search your knowledge vault using hybrid semantic and keyword matching.
    
    This tool combines semantic vector search with keyword matching to find the most relevant
    information in your personal knowledge vault. It uses a two-stage process:
    1. Generates candidate matches using both semantic understanding and keyword relevance
    2. Applies a reranking model to return the top most relevant results
    
    Args:
        query: Natural language query for semantic search and reranking
        user_id: Your unique user identifier
        keywords: Specific terms to prioritize in keyword matching (optional)
        top_k: Number of results to return (default: 10)
    
    Returns:
        A formatted string containing the most relevant results from your knowledge vault
    """
    # print(f"Tool called with query: {query}, user_id: {user_id}", file=sys.stderr)
    
    try:
        # Prepare the API endpoint URL
        endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/knowledge/search_knowledge_vault"
        
        # Prepare the request payload
        payload = {
            "query": query,
            "keywords": keywords,
            "top_k": top_k
        }
        
        print(f"Calling API endpoint: {endpoint}", file=sys.stderr)
        
        # Make the API request
        response = await make_fondu_api_request(
            url=endpoint,
            method="POST",
            json_data=payload
        )
        
        if response is None:
            return "Error: Failed to get a response from the knowledge vault API."
        
        # Extract results from the response
        results = response.get("results", [])
        count = response.get("count", 0)
        
        print(f"Search completed successfully, found {count} results", file=sys.stderr)
        
        # Format the results into a string
        if count == 0:
            return "No relevant information found in your knowledge vault."
        
        # Return formatted results
        return_text = f"Found {count} relevant results in your knowledge vault:\n\n"
        for i, result in enumerate(results, 1):
            # Handle different possible result formats
            if isinstance(result, dict):
                # Extract relevant fields if result is a dictionary
                text = result.get("text", "")
                source = result.get("source", "")
                metadata = result.get("metadata", {})
                
                return_text += f"{i}. "
                if text:
                    return_text += f"{text}\n"
                if source:
                    return_text += f"Source: {source}\n"
                if metadata:
                    return_text += f"Metadata: {metadata}\n"
            else:
                # If result is a string or other format
                return_text += f"{i}. {result}\n"
            
            return_text += "\n"
        
        return return_text
        
    except Exception as e:
        error_msg = f"Error performing knowledge vault search: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        return f"Error performing knowledge vault search: {str(e)}"

# @mcp.tool()
# async def get_canvas_courses(include_details: bool = False) -> str:
#     """Get your Canvas LMS courses.
    
#     This tool connects to your Canvas Learning Management System account and retrieves a list
#     of your current courses. It can optionally include additional details about each course.
    
#     Args:
#         include_details: Whether to include additional details about each course (default: False)
    
#     Returns:
#         A formatted string containing your Canvas courses
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/courses?access_token={user_token}"
        
#         if include_details:
#             # Add additional parameters if needed
#             endpoint += "&enrollment_state=active"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request (now using GET instead of POST)
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return "Error: Failed to get a response from the Canvas API."
        
#         # Extract courses from the response
#         courses = response if isinstance(response, list) else []
#         count = len(courses)
        
#         print(f"Canvas API call completed successfully, found {count} courses", file=sys.stderr)
        
#         # Format the results into a string
#         if count == 0:
#             return "No courses found in your Canvas account."
        
#         # Return formatted results
#         return_text = f"Found {count} courses in your Canvas account:\n\n"
#         for i, course in enumerate(courses, 1):
#             course_name = course.get("name", "Unnamed Course")
#             course_code = course.get("course_code", "No Code")
#             course_id = course.get("id", "No ID")
            
#             return_text += f"{i}. {course_name} ({course_code})\n"
#             return_text += f"   ID: {course_id}\n"
            
#             if include_details:
#                 start_date = course.get("start_at", "Not specified")
#                 end_date = course.get("end_at", "Not specified")
#                 enrollment_term = course.get("enrollment_term_id", "Default Term")
#                 syllabus = course.get("syllabus_body")
                
#                 return_text += f"   Start Date: {start_date}\n"
#                 return_text += f"   End Date: {end_date}\n"
#                 return_text += f"   Term: {enrollment_term}\n"
                
#                 if syllabus:
#                     return_text += f"   Has Syllabus: Yes\n"
            
#             return_text += "\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas courses: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas courses: {str(e)}"

# # @mcp.tool()
# # async def get_canvas_assignments(course_id: str, include_details: bool = False) -> str:
# #     """Get assignments for a specific Canvas LMS course.
    
# #     This tool retrieves a list of assignments for a specified course from your Canvas
# #     Learning Management System account.
    
# #     Args:
# #         course_id: The Canvas course ID
# #         include_details: Whether to include additional details about each assignment (default: False)
    
# #     Returns:
# #         A formatted string containing the course assignments
# #     """
# #     try:
# #         # Use hardcoded token for authentication as specified
# #         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
# #         # Prepare the API endpoint URL with query parameters
# #         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/courses/{course_id}/assignments?access_token={user_token}"
        
# #         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
# #         # Make the API request (now using GET instead of POST)
# #         response = await make_fondu_api_request(
# #             url=endpoint,
# #             method="GET"
# #         )
        
# #         if response is None:
# #             return f"Error: Failed to get a response from the Canvas API for course {course_id}."
        
# #         # Extract assignments from the response
# #         assignments = response if isinstance(response, list) else []
# #         count = len(assignments)
        
# #         print(f"Canvas API call completed successfully, found {count} assignments", file=sys.stderr)
        
# #         # Format the results into a string
# #         if count == 0:
# #             return f"No assignments found for course {course_id}."
        
# #         # Return formatted results
# #         return_text = f"Found {count} assignments for course {course_id}:\n\n"
# #         for i, assignment in enumerate(assignments, 1):
# #             name = assignment.get("name", "Unnamed Assignment")
# #             due_date = assignment.get("due_at", "No due date")
# #             points = assignment.get("points_possible", "Not specified")
            
# #             return_text += f"{i}. {name}\n"
# #             return_text += f"   Due: {due_date}\n"
# #             return_text += f"   Points: {points}\n"
            
# #             if include_details:
# #                 description = assignment.get("description", "No description")
# #                 submission_types = assignment.get("submission_types", [])
                
# #                 # Truncate description if too long
# #                 if description and len(description) > 200:
# #                     description = description[:200] + "..."
                
# #                 return_text += f"   Submission Types: {', '.join(submission_types) if isinstance(submission_types, list) else submission_types}\n"
# #                 if description != "No description":
# #                     return_text += f"   Description: {description}\n"
            
# #             return_text += "\n"
        
# #         return return_text
        
# #     except Exception as e:
# #         error_msg = f"Error retrieving Canvas assignments: {str(e)}\n{traceback.format_exc()}"
# #         print(error_msg, file=sys.stderr)
# #         return f"Error retrieving Canvas assignments: {str(e)}"

# @mcp.tool()
# async def get_canvas_modules(course_id: str) -> str:
#     """Get modules for a specific Canvas LMS course.
    
#     This tool retrieves a list of modules and their items for a specified course from your Canvas
#     Learning Management System account.
    
#     Args:
#         course_id: The Canvas course ID
    
#     Returns:
#         A formatted string containing the course modules and their contents
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/courses/{course_id}/modules?access_token={user_token}"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request (now using GET instead of POST)
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return f"Error: Failed to get a response from the Canvas API for course {course_id}."
        
#         # Extract modules from the response
#         modules = response if isinstance(response, list) else []
#         count = len(modules)
        
#         print(f"Canvas API call completed successfully, found {count} modules", file=sys.stderr)
        
#         # Format the results into a string
#         if count == 0:
#             return f"No modules found for course {course_id}."
        
#         # Return formatted results
#         return_text = f"Found {count} modules for course {course_id}:\n\n"
#         for i, module in enumerate(modules, 1):
#             name = module.get("name", "Unnamed Module")
#             unlock_date = module.get("unlock_at", "Not specified")
#             items_count = len(module.get("items", []))
            
#             return_text += f"{i}. {name}\n"
#             return_text += f"   Unlock Date: {unlock_date}\n"
#             return_text += f"   Items: {items_count}\n"
            
#             # List module items if available
#             items = module.get("items", [])
#             if items:
#                 return_text += "   Contents:\n"
#                 for j, item in enumerate(items, 1):
#                     item_name = item.get("title", "Unnamed Item")
#                     item_type = item.get("type", "Unknown Type")
#                     return_text += f"     {j}. {item_name} ({item_type})\n"
            
#             return_text += "\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas modules: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas modules: {str(e)}"

# @mcp.tool()
# async def get_canvas_user_profile() -> str:
#     """Get your Canvas LMS user profile.
    
#     This tool retrieves your user profile information from Canvas Learning Management System.
    
#     Returns:
#         A formatted string containing your Canvas user profile information
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/profile?access_token={user_token}"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return "Error: Failed to get a response from the Canvas API."
        
#         # Format the profile information
#         profile_id = response.get("id", "Unknown")
#         name = response.get("name", "Unknown Name")
#         email = response.get("email", "No email provided")
#         avatar_url = response.get("avatar_url", "No avatar")
        
#         return_text = "Canvas User Profile:\n\n"
#         return_text += f"ID: {profile_id}\n"
#         return_text += f"Name: {name}\n"
        
#         if email != "No email provided":
#             return_text += f"Email: {email}\n"
        
#         if "short_name" in response:
#             return_text += f"Short Name: {response['short_name']}\n"
        
#         if "sortable_name" in response:
#             return_text += f"Sortable Name: {response['sortable_name']}\n"
        
#         return_text += f"Avatar URL: {avatar_url}\n"
        
#         # Include any additional data if available
#         additional_data = response.get("additional_data", {})
#         if additional_data:
#             return_text += "\nAdditional Information:\n"
#             for key, value in additional_data.items():
#                 return_text += f"{key}: {value}\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas user profile: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas user profile: {str(e)}"

# @mcp.tool()
# async def get_canvas_user_assignments(course_id: str, include_details: bool = False) -> str:
#     """Get your assignments for a specific Canvas LMS course.
    
#     This tool retrieves a list of assignments for you (user ID 155332) in a specified course.
    
#     Args:
#         course_id: The Canvas course ID
#         include_details: Whether to include additional details about each assignment (default: False)
    
#     Returns:
#         A formatted string containing your course assignments
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Ensure course_id is clean (no quotes)
#         clean_course_id = course_id.strip('"\'')
        
#         # The user_id is hardcoded to 155332 in the API
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/users/155332/courses/{clean_course_id}/assignments?access_token={user_token}&canvas_domain=boisestatecanvas.instructure.com"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request (now using GET instead of POST)
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return f"Error: Failed to get a response from the Canvas API for course {clean_course_id}."
        
#         # Extract assignments from the response
#         assignments = response if isinstance(response, list) else []
#         count = len(assignments)
        
#         print(f"Canvas API call completed successfully, found {count} user assignments", file=sys.stderr)
        
#         # Format the results into a string
#         if count == 0:
#             return f"No assignments found for user 155332 in course {clean_course_id}."
        
#         # Return formatted results
#         return_text = f"Found {count} assignments for user 155332 in course {clean_course_id}:\n\n"
#         for i, assignment in enumerate(assignments, 1):
#             name = assignment.get("name", "Unnamed Assignment")
#             due_date = assignment.get("due_at", "No due date")
#             points = assignment.get("points_possible", "Not specified")
            
#             return_text += f"{i}. {name}\n"
#             return_text += f"   Due: {due_date}\n"
#             return_text += f"   Points: {points}\n"
            
#             if include_details:
#                 description = assignment.get("description", "No description")
#                 submission_types = assignment.get("submission_types", [])
#                 submission = assignment.get("submission", {})
#                 grade = submission.get("grade", "Not graded")
#                 score = submission.get("score", "No score")
                
#                 # Truncate description if too long
#                 if description and len(description) > 200:
#                     description = description[:200] + "..."
                
#                 return_text += f"   Submission Types: {', '.join(submission_types) if isinstance(submission_types, list) else submission_types}\n"
#                 if grade != "Not graded":
#                     return_text += f"   Grade: {grade}\n"
#                 if score != "No score":
#                     return_text += f"   Score: {score}\n"
#                 if description != "No description":
#                     return_text += f"   Description: {description}\n"
            
#             return_text += "\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas user assignments: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas user assignments: {str(e)}"

# @mcp.tool()
# async def get_canvas_user_grades(course_id: str) -> str:
#     """Get your grades for a specific Canvas LMS course.
    
#     This tool retrieves your grades (user ID 155332) for a specified course.
    
#     Args:
#         course_id: The Canvas course ID
    
#     Returns:
#         A formatted string containing your course grades
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Ensure course_id is clean (no quotes)
#         clean_course_id = course_id.strip('"\'')
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/user/courses/{clean_course_id}/grades?access_token={user_token}&canvas_domain=boisestatecanvas.instructure.com"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return f"Error: Failed to get a response from the Canvas API for course {clean_course_id}."
        
#         # Extract grades from the response
#         course_name = response.get("name", "Unknown Course")
#         enrollments = response.get("enrollments", [])
        
#         if not enrollments:
#             return f"No grade information found for course {clean_course_id}."
        
#         # Return formatted results
#         return_text = f"Grades for course: {course_name} (ID: {clean_course_id})\n\n"
        
#         for enrollment in enrollments:
#             type_name = enrollment.get("type", "Unknown enrollment type")
#             current_grade = enrollment.get("current_grade", "No grade")
#             current_score = enrollment.get("current_score", "No score")
#             final_grade = enrollment.get("final_grade", "No final grade")
#             final_score = enrollment.get("final_score", "No final score")
            
#             return_text += f"Enrollment Type: {type_name}\n"
            
#             if current_grade != "No grade":
#                 return_text += f"Current Grade: {current_grade}\n"
            
#             if current_score != "No score":
#                 return_text += f"Current Score: {current_score}\n"
            
#             if final_grade != "No final grade":
#                 return_text += f"Final Grade: {final_grade}\n"
            
#             if final_score != "No final score":
#                 return_text += f"Final Score: {final_score}\n"
        
#         # Add any additional information if available
#         if "total_scores" in response:
#             return_text += "\nAssignment Scores:\n"
#             for assignment in response.get("assignments", []):
#                 name = assignment.get("name", "Unknown Assignment")
#                 score = assignment.get("score", "Not scored")
#                 points_possible = assignment.get("points_possible", "Unknown points")
                
#                 return_text += f"- {name}: {score}/{points_possible}\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas user grades: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas user grades: {str(e)}"

# @mcp.tool()
# async def get_canvas_modules_detailed(
#     course_id: str, 
#     include_items: bool = False, 
#     include_content_details: bool = False,
#     search_term: str = "",
#     get_completion_info: bool = False
# ) -> str:
#     """Get detailed information about modules in a Canvas LMS course.
    
#     This tool retrieves a list of modules for a specified course with additional options
#     to include module items, content details, filter by name, and get completion information.
    
#     Args:
#         course_id: The Canvas course ID
#         include_items: Whether to include module items (default: False)
#         include_content_details: Whether to include content details for items (default: False)
#         search_term: Filter modules by partial name match (default: "")
#         get_completion_info: Whether to include completion information for the user (default: False)
    
#     Returns:
#         A formatted string containing the course modules with requested details
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Ensure course_id is clean (no quotes)
#         clean_course_id = course_id.strip('"\'')
        
#         # Build the query parameters
#         params = f"access_token={user_token}&canvas_domain=boisestatecanvas.instructure.com"
        
#         # Add optional parameters
#         include_params = []
#         if include_items:
#             include_params.append("items")
#         if include_content_details and include_items:  # content_details requires items
#             include_params.append("content_details")
            
#         if include_params:
#             params += f"&include[]={','.join(include_params)}"
            
#         if search_term:
#             params += f"&search_term={search_term}"
            
#         if get_completion_info:
#             params += "&student_id=155332"  # Hardcoded user ID
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/courses/{clean_course_id}/modules?{params}"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request (using GET)
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return f"Error: Failed to get a response from the Canvas API for course {clean_course_id}."
        
#         # Extract modules from the response
#         modules = response if isinstance(response, list) else []
#         count = len(modules)
        
#         print(f"Canvas API call completed successfully, found {count} modules", file=sys.stderr)
        
#         # Format the results into a string
#         if count == 0:
#             return f"No modules found for course {clean_course_id}."
        
#         # Return formatted results
#         return_text = f"Found {count} modules for course {clean_course_id}"
#         if search_term:
#             return_text += f" matching '{search_term}'"
#         return_text += ":\n\n"
        
#         for i, module in enumerate(modules, 1):
#             name = module.get("name", "Unnamed Module")
#             unlock_date = module.get("unlock_at", "Not specified")
#             state = module.get("state", "Unknown state")
#             position = module.get("position", "Unknown position")
            
#             return_text += f"{i}. {name}\n"
#             return_text += f"   ID: {module.get('id', 'Unknown')}\n"
#             return_text += f"   State: {state}\n"
#             return_text += f"   Position: {position}\n"
#             return_text += f"   Unlock Date: {unlock_date}\n"
            
#             # Include completion information if available
#             if get_completion_info:
#                 completed = module.get("completed", False)
#                 return_text += f"   Completed: {completed}\n"
                
#                 completion_requirements = module.get("completion_requirements", [])
#                 if completion_requirements:
#                     return_text += f"   Completion Requirements: {len(completion_requirements)}\n"
            
#             # List module items if available
#             items = module.get("items", [])
#             if items and include_items:
#                 return_text += f"   Items ({len(items)}):\n"
#                 for j, item in enumerate(items, 1):
#                     item_name = item.get("title", "Unnamed Item")
#                     item_type = item.get("type", "Unknown Type")
#                     item_id = item.get("id", "Unknown ID")
                    
#                     return_text += f"     {j}. {item_name} ({item_type})\n"
                    
#                     # Include content details if available
#                     if include_content_details:
#                         content_details = item.get("content_details", {})
#                         if content_details:
#                             due_at = content_details.get("due_at", "No due date")
#                             points_possible = content_details.get("points_possible", "Not specified")
#                             return_text += f"        Due: {due_at}\n"
#                             return_text += f"        Points: {points_possible}\n"
            
#             return_text += "\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving detailed Canvas modules: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving detailed Canvas modules: {str(e)}"

# @mcp.tool()
# async def get_canvas_module_items(
#     course_id: str,
#     module_id: str,
#     include_content_details: bool = False,
#     get_completion_info: bool = False
# ) -> str:
#     """Get items in a specific Canvas LMS module.
    
#     This tool retrieves a list of items for a specific module in a course.
    
#     Args:
#         course_id: The Canvas course ID
#         module_id: The Canvas module ID
#         include_content_details: Whether to include content details for items (default: False)
#         get_completion_info: Whether to include completion information for the user (default: False)
    
#     Returns:
#         A formatted string containing the module items with requested details
#     """
#     try:
#         # Use hardcoded token for authentication as specified
#         user_token = "15177~LFNQt7ERtvz8KmFtmkeNYvfzhwXQ7ekuJztJx6E3JL6U9MemRZDDzJXeLcvetQP9"
        
#         # Ensure IDs are clean (no quotes)
#         clean_course_id = course_id.strip('"\'')
#         clean_module_id = module_id.strip('"\'')
        
#         # Build the query parameters
#         params = f"access_token={user_token}&canvas_domain=boisestatecanvas.instructure.com"
        
#         # Add optional parameters
#         if include_content_details:
#             params += "&include[]=content_details"
            
#         if get_completion_info:
#             params += "&student_id=155332"  # Hardcoded user ID
        
#         # Prepare the API endpoint URL with query parameters
#         endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/canvas/courses/{clean_course_id}/modules/{clean_module_id}/items?{params}"
        
#         print(f"Calling Canvas API endpoint: {endpoint}", file=sys.stderr)
        
#         # Make the API request (using GET)
#         response = await make_fondu_api_request(
#             url=endpoint,
#             method="GET"
#         )
        
#         if response is None:
#             return f"Error: Failed to get a response from the Canvas API for module {clean_module_id} in course {clean_course_id}."
        
#         # Extract items from the response
#         items = response if isinstance(response, list) else []
#         count = len(items)
        
#         print(f"Canvas API call completed successfully, found {count} module items", file=sys.stderr)
        
#         # Format the results into a string
#         if count == 0:
#             return f"No items found for module {clean_module_id} in course {clean_course_id}."
        
#         # Return formatted results
#         return_text = f"Found {count} items for module {clean_module_id} in course {clean_course_id}:\n\n"
        
#         for i, item in enumerate(items, 1):
#             title = item.get("title", "Unnamed Item")
#             item_type = item.get("type", "Unknown Type")
#             item_id = item.get("id", "Unknown ID")
#             url = item.get("html_url", "No URL")
            
#             return_text += f"{i}. {title}\n"
#             return_text += f"   ID: {item_id}\n"
#             return_text += f"   Type: {item_type}\n"
#             return_text += f"   URL: {url}\n"
            
#             # Include completion information if available
#             if get_completion_info:
#                 completion_requirement = item.get("completion_requirement", {})
#                 if completion_requirement:
#                     req_type = completion_requirement.get("type", "Unknown")
#                     completed = completion_requirement.get("completed", False)
#                     return_text += f"   Completion Type: {req_type}\n"
#                     return_text += f"   Completed: {completed}\n"
            
#             # Include content details if available
#             if include_content_details:
#                 content_details = item.get("content_details", {})
#                 if content_details:
#                     due_at = content_details.get("due_at", "No due date")
#                     points_possible = content_details.get("points_possible", "Not specified")
                    
#                     return_text += f"   Due: {due_at}\n"
#                     if points_possible != "Not specified":
#                         return_text += f"   Points: {points_possible}\n"
                    
#                     # Include submission info if available
#                     if "submission" in content_details:
#                         submission = content_details.get("submission", {})
#                         submitted = submission.get("submitted_at", "Not submitted")
#                         grade = submission.get("grade", "Not graded")
#                         score = submission.get("score", "No score")
                        
#                         if submitted != "Not submitted":
#                             return_text += f"   Submitted: {submitted}\n"
#                         if grade != "Not graded":
#                             return_text += f"   Grade: {grade}\n"
#                         if score != "No score":
#                             return_text += f"   Score: {score}\n"
            
#             return_text += "\n"
        
#         return return_text
        
#     except Exception as e:
#         error_msg = f"Error retrieving Canvas module items: {str(e)}\n{traceback.format_exc()}"
#         print(error_msg, file=sys.stderr)
#         return f"Error retrieving Canvas module items: {str(e)}"

# Add FastAPI endpoints
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/mcp")
async def handle_mcp_request(request: Request):
    try:
        body = await request.json()
        # Pass the request to MCP for processing
        result = await mcp.process_json_request(body)
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Error handling MCP request: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    try:
        # Get port from environment variable or use default
        port = int(os.environ.get("PORT", 8080))
        
        # Start the FastAPI server with uvicorn
        print(f"Starting FastAPI server on port {port}", file=sys.stderr)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        error_msg = f"Fatal error in MCP server: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        sys.exit(1) 