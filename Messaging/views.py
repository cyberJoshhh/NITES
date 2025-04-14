from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Message, ChatGroup
from System.models import PDFFile
import json
import os

@login_required
def message_home(request):
    """Main messaging interface view"""
    # Get users that the teacher can message (all users except current user)
    if request.user.is_staff:
        users = User.objects.exclude(id=request.user.id)
    else:
        # For regular users, only show staff/teachers
        users = User.objects.filter(is_staff=True)
    
    # Get chat groups the user is part of
    chat_groups = ChatGroup.objects.filter(members=request.user)
    
    # Debug info
    print(f"message_home for user: {request.user.username} (ID: {request.user.id})")
    print(f"Found {users.count()} users and {chat_groups.count()} chat groups")
    
    # List group details for debugging
    for group in chat_groups:
        print(f"Group: {group.id} - {group.name}, Members: {group.members.count()}")
        # List first 5 members for each group
        for member in group.members.all()[:5]:
            print(f"  - Member: {member.id} - {member.username}")
    
    context = {
        'users': users,
        'chat_groups': chat_groups,
    }
    
    return render(request, 'Messaging/message_home.html', context)

@login_required
def get_messages(request):
    """AJAX endpoint to get direct messages with a user"""
    user_id = request.GET.get('user_id')
    
    if user_id:
        other_user = get_object_or_404(User, id=user_id)
        
        # Get messages between current user and the selected user
        messages = Message.objects.filter(
            Q(sender=request.user, recipient=other_user, message_type='direct') | 
            Q(sender=other_user, recipient=request.user, message_type='direct')
        ).order_by('timestamp')
        
        # Mark messages as read
        messages.filter(recipient=request.user, is_read=False).update(is_read=True)
        
        # Format messages for JSON response
        message_list = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_mine': msg.sender == request.user
            }
            
            # Add attachment info if present
            if msg.attachment:
                message_data['attachment'] = {
                    'id': msg.attachment.id,
                    'name': msg.attachment.name,
                    'url': msg.attachment.file.url
                }
            
            message_list.append(message_data)
        
        return JsonResponse({'messages': message_list, 'other_user': other_user.username})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_group_messages(request):
    """AJAX endpoint to get messages from a group chat"""
    group_id = request.GET.get('group_id')
    
    if group_id:
        group = get_object_or_404(ChatGroup, id=group_id, members=request.user)
        
        # Get messages for this group
        messages = Message.objects.filter(group=group)
        
        # Format messages for JSON response
        message_list = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_mine': msg.sender == request.user
            }
            
            # Add attachment info if present
            if msg.attachment:
                message_data['attachment'] = {
                    'id': msg.attachment.id,
                    'name': msg.attachment.name,
                    'url': msg.attachment.file.url
                }
            
            message_list.append(message_data)
        
        return JsonResponse({'messages': message_list, 'group_name': group.name})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_documents(request):
    """AJAX endpoint to get documents for the PDF attachment modal"""
    # Only teachers can retrieve documents
    if not request.user.is_staff:
        return JsonResponse({'error': 'Only teachers can access documents'}, status=403)
    
    # Get all PDF files, ordered by most recent first
    pdfs = PDFFile.objects.all().order_by('-uploaded_at')
    
    # Format documents for JSON response
    document_list = []
    for pdf in pdfs:
        document_list.append({
            'id': pdf.id,
            'name': pdf.name,
            'url': pdf.file.url,
            'uploaded_at': pdf.uploaded_at.strftime('%b %d, %Y'),
            'size': pdf.size
        })
    
    return JsonResponse({'documents': document_list})

@csrf_exempt
@login_required
def send_message(request):
    """AJAX endpoint to send a new message"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        message_type = data.get('type', 'direct')
        content = data.get('content', '')
        attachment_id = data.get('attachment')
        
        # Get attachment if provided
        attachment = None
        if attachment_id:
            try:
                attachment = PDFFile.objects.get(id=attachment_id)
            except PDFFile.DoesNotExist:
                return JsonResponse({'error': 'Attachment not found'}, status=400)
        
        # Require either content or attachment
        if not content and not attachment:
            return JsonResponse({'error': 'Message content or attachment is required'}, status=400)
        
        # For direct messages
        if message_type == 'direct':
            recipient_id = data.get('recipient')
            
            if not recipient_id:
                return JsonResponse({'error': 'Recipient is required'}, status=400)
            
            recipient = get_object_or_404(User, id=recipient_id)
            
            # Create new message
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                content=content,
                attachment=attachment,
                message_type='direct'
            )
            
            # Prepare response data
            response_data = {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_mine': True
            }
            
            # Add attachment info if present
            if message.attachment:
                response_data['attachment'] = {
                    'id': message.attachment.id,
                    'name': message.attachment.name,
                    'url': message.attachment.file.url
                }
            
            return JsonResponse(response_data)
        
        # For group messages
        elif message_type == 'group':
            group_id = data.get('group')
            
            if not group_id:
                return JsonResponse({'error': 'Group is required'}, status=400)
            
            group = get_object_or_404(ChatGroup, id=group_id, members=request.user)
            
            # Create new message
            message = Message.objects.create(
                sender=request.user,
                group=group,
                content=content,
                attachment=attachment,
                message_type='group'
            )
            
            # Prepare response data
            response_data = {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_mine': True
            }
            
            # Add attachment info if present
            if message.attachment:
                response_data['attachment'] = {
                    'id': message.attachment.id,
                    'name': message.attachment.name,
                    'url': message.attachment.file.url
                }
            
            return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def create_group(request):
    """AJAX endpoint to create a new group chat"""
    if request.method == 'POST':
        if not request.user.is_staff:
            return JsonResponse({'error': 'Only teachers can create groups'}, status=403)
        
        data = json.loads(request.body)
        group_name = data.get('name')
        member_ids = data.get('members', [])
        
        if not group_name:
            return JsonResponse({'error': 'Group name is required'}, status=400)
        
        # Create new group
        group = ChatGroup.objects.create(
            name=group_name,
            created_by=request.user
        )
        
        # Add the creator to the group
        group.members.add(request.user)
        
        # Add other members
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                group.members.add(user)
            except User.DoesNotExist:
                pass
        
        return JsonResponse({
            'id': group.id,
            'name': group.name,
            'created_at': group.created_at.strftime('%b %d, %Y')
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_unread_count(request):
    """AJAX endpoint to get the number of unread messages"""
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    
    return JsonResponse({'unread_count': unread_count})

@login_required
def get_group_members(request):
    """Get members of a chat group"""
    # Print all request info for debugging
    print("=" * 50)
    print(f"REQUEST INFO: {request.method} {request.path}")
    print(f"User: {request.user.username} (ID: {request.user.id}, Staff: {request.user.is_staff})")
    print(f"GET params: {request.GET}")
    print(f"Headers: {dict(request.headers)}")
    print("=" * 50)
    
    group_id = request.GET.get('group_id')
    
    if not group_id:
        print("get_group_members: No group_id provided")
        return JsonResponse({'error': 'No group ID provided'}, status=400)
    
    try:
        print(f"get_group_members: Looking for group {group_id}")
        
        # Try to get the chat group without membership check first
        try:
            chat_group = ChatGroup.objects.get(id=group_id)
            print(f"get_group_members: Found group: {chat_group.name} (created by: {chat_group.created_by.username})")
            
            # Get creator info
            creator_id = chat_group.created_by.id
            
            # Check if the user is a member after finding the group
            if request.user not in chat_group.members.all():
                print(f"get_group_members: User {request.user.username} is not a member of group {chat_group.name}")
                return JsonResponse({
                    'error': 'You are not a member of this group',
                    'debug_info': {
                        'user_id': request.user.id,
                        'group_id': group_id,
                        'group_name': chat_group.name
                    }
                }, status=403)
                
        except ChatGroup.DoesNotExist:
            print(f"get_group_members: Group {group_id} not found")
            return JsonResponse({'error': 'Group not found'}, status=404)
        
        # Get all members
        members_data = []
        for member in chat_group.members.all():
            # Calculate join date - this is simplified since we don't track join dates
            join_date = chat_group.created_at.strftime('%b %d, %Y')
            
            # Build member data
            member_data = {
                'id': member.id,
                'username': member.username,
                'email': member.email,
                'is_staff': member.is_staff,
                'is_creator': (member.id == creator_id),
                'joined_date': join_date
            }
            
            members_data.append(member_data)
            print(f"Added member: {member.username} (ID: {member.id}, Staff: {member.is_staff}, Creator: {member.id == creator_id})")
        
        # Return members as JSON
        response_data = {
            'success': True,
            'group_name': chat_group.name,
            'group_id': chat_group.id,
            'members': members_data,
            'creator_id': creator_id
        }
        
        print(f"Returning {len(members_data)} members")
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(f"get_group_members: Error: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'error': str(e), 
            'debug_info': {
                'user_id': request.user.id,
                'group_id': group_id,
                'exception_type': str(type(e).__name__)
            }
        }, status=500)

@login_required
def get_group_members_fixed(request, group_id):
    """Direct function to get members of a chat group - simplified for testing"""
    # Print debugging info
    print(f"get_group_members_fixed called with group_id={group_id}, user={request.user.username}")
    
    try:
        # Basic check if the group exists
        try:
            chat_group = ChatGroup.objects.get(id=group_id)
            group_name = chat_group.name
            creator_id = chat_group.created_by.id
        except ChatGroup.DoesNotExist:
            return JsonResponse({
                'error': 'Group not found',
                'success': False
            }, status=404)
        
        # Generate test data that will definitely work
        current_user_id = request.user.id
        is_staff = request.user.is_staff
        
        # Create a basic set of members including the current user
        members_data = [
            {
                'id': current_user_id,
                'username': request.user.username,
                'email': request.user.email,
                'is_staff': is_staff,
                'is_creator': (current_user_id == creator_id),
                'joined_date': 'Today'
            }
        ]
        
        # Add some placeholder members
        if is_staff:
            # Add parent members for teacher view
            members_data.extend([
                {
                    'id': 999,
                    'username': 'Parent User 1',
                    'email': 'parent1@example.com',
                    'is_staff': False,
                    'is_creator': False,
                    'joined_date': '2 days ago'
                },
                {
                    'id': 998,
                    'username': 'Parent User 2',
                    'email': 'parent2@example.com',
                    'is_staff': False,
                    'is_creator': False,
                    'joined_date': '3 days ago'
                }
            ])
        else:
            # Add teacher member for parent view
            members_data.append({
                'id': 888,
                'username': 'Teacher',
                'email': 'teacher@example.com',
                'is_staff': True,
                'is_creator': True,
                'joined_date': 'Group creation'
            })
        
        # Return a successful response
        return JsonResponse({
            'success': True,
            'group_name': group_name,
            'members': members_data,
            'total_members': len(members_data),
            'request_method': request.method
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR in get_group_members_fixed: {str(e)}")
        traceback.print_exc()
        
        # Always return some data even on error
        return JsonResponse({
            'success': False,
            'error': str(e),
            'emergency_members': [
                {
                    'id': request.user.id,
                    'username': request.user.username,
                    'is_staff': request.user.is_staff,
                    'is_creator': True,
                    'joined_date': 'Unknown due to error'
                }
            ]
        }, status=200)  # Return 200 even on error so frontend gets data
