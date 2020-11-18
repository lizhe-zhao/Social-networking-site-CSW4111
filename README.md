# w4111-proj1-part3
Team member: lz2766 Lizhe Zhao
		         xz2987 Xiaoshu Zhao
Account: xz2987
URL:
Feature implemented:
                    Login: if your post anything that requires sid, and it is not in the Database, redirect to a login page, where your information will be added to Database.
                    Profile: input sid and email, if not match return error message; if match, redirect to profile page where you can see your posts, events attended and hosted and events at your location. location can be updated at this page.
                    Events and Posts: a page listed all events and all posts. Can be sorted based on time and popularity (popularity=# of up votes-# of down votes). Add new event or post at this page.
                    Detail pages of a post: details of a post including votes, post student name, post time, content. You can leave your comment for this post and vote up/down.
                    Detail page for an event: details of an event including host(s), start and end time, votes, description and location. You can leave your comment for this event and vote up/down. Also, you can join/leave the list for this event, or become a cohost of the event.
Detail pages and the pages that lists all events and posts are the most interesting pages.
1. pass pid or eid into flask function from previous page and select corresponding information
2. sort function provide options that users can select. It counts number of different votes and rank items, and sort based on date and time
3. add new post/event function will insert new tuples into the database
4. if the input sid is not found in the database, user will be redirected to login page.
These pages contains most of the functions we want to implement and interacts with our database a lot. Some new features like drop down select options are new to us and require a lot of search online.

                    
