/**
 * Messaging functionality for the chat system
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing messaging functionality');
    
    // DOM elements
    const contactItems = document.querySelectorAll('.contact-item');
    const groupItems = document.querySelectorAll('.group-item');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatInterface = document.querySelector('.chat-interface');
    const chatName = document.getElementById('chatName');
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    
    // Debug DOM elements
    console.log('Contact items found:', contactItems.length);
    console.log('Group items found:', groupItems.length);
    console.log('Welcome screen found:', welcomeScreen !== null);
    console.log('Chat interface found:', chatInterface !== null);
    console.log('Message form found:', messageForm !== null);
    
    // Current chat state
    let currentChat = {
        type: null, // 'direct' or 'group'
        id: null
    };
    
    // Initialize unread message count
    function updateUnreadCounts() {
        fetch('/messaging/get_unread_count/')
            .then(response => response.json())
            .then(data => {
                console.log('Unread count:', data.unread_count);
                const totalCount = data.unread_count;
                // Update the messages link in the sidebar if it exists
                const messagesLink = document.querySelector('.sidebar-btn i.fas.fa-envelope');
                if (messagesLink && totalCount > 0) {
                    // Add or update badge
                    let badge = messagesLink.parentNode.querySelector('.badge');
                    if (!badge) {
                        badge = document.createElement('span');
                        badge.className = 'badge badge-danger ml-2';
                        messagesLink.parentNode.appendChild(badge);
                    }
                    badge.textContent = totalCount;
                }
            })
            .catch(error => console.error('Error fetching unread count:', error));
    }
    
    // Poll for unread messages every 30 seconds
    updateUnreadCounts();
    setInterval(updateUnreadCounts, 30000);
    
    // Handle contact selection - using event delegation for better compatibility
    document.addEventListener('click', function(e) {
        // Check if clicked element is a contact item or its child
        const contactItem = e.target.closest('.contact-item');
        const groupItem = e.target.closest('.group-item');
        
        if (contactItem) {
            console.log('Contact clicked:', contactItem.querySelector('span').textContent);
            e.preventDefault();
            
            // Clear active state from all items
            contactItems.forEach(contact => contact.classList.remove('active'));
            groupItems.forEach(group => group.classList.remove('active'));
            
            // Set this contact as active
            contactItem.classList.add('active');
            
            // Show chat interface
            if (welcomeScreen) welcomeScreen.classList.add('d-none');
            if (chatInterface) {
                chatInterface.classList.remove('d-none');
                console.log('Chat interface should be visible now');
            }
            
            // Set current chat
            const userId = contactItem.getAttribute('data-id');
            if (userId) {
                currentChat = {
                    type: 'direct',
                    id: userId
                };
                
                // Load messages
                loadDirectMessages(userId);
            } else {
                console.error('No user ID found on contact item');
            }
        }
        else if (groupItem) {
            console.log('Group clicked:', groupItem.querySelector('span').textContent);
            e.preventDefault();
            
            // Clear active state from all items
            contactItems.forEach(contact => contact.classList.remove('active'));
            groupItems.forEach(group => group.classList.remove('active'));
            
            // Set this group as active
            groupItem.classList.add('active');
            
            // Show chat interface
            if (welcomeScreen) welcomeScreen.classList.add('d-none');
            if (chatInterface) {
                chatInterface.classList.remove('d-none');
                console.log('Chat interface should be visible now');
            }
            
            // Set current chat
            const groupId = groupItem.getAttribute('data-id');
            if (groupId) {
                currentChat = {
                    type: 'group',
                    id: groupId
                };
                
                // Load messages
                loadGroupMessages(groupId);
            } else {
                console.error('No group ID found on group item');
            }
        }
    });
    
    // Load direct messages
    function loadDirectMessages(userId) {
        console.log('Loading direct messages for user ID:', userId);
        fetch(`/messaging/get_messages/?user_id=${userId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Messages loaded:', data.messages.length);
                // Update chat name
                if (chatName) chatName.textContent = data.other_user;
                
                // Clear existing messages
                if (messageContainer) messageContainer.innerHTML = '';
                
                // Add messages to container
                data.messages.forEach(message => {
                    addMessageToContainer(message);
                });
                
                // Scroll to bottom
                scrollToBottom();
            })
            .catch(error => console.error('Error loading messages:', error));
    }
    
    // Load group messages
    function loadGroupMessages(groupId) {
        console.log('Loading group messages for group ID:', groupId);
        fetch(`/messaging/get_group_messages/?group_id=${groupId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Group messages loaded:', data.messages ? data.messages.length : 0);
                // Update chat name
                if (chatName) chatName.textContent = data.group_name;
                
                // Clear existing messages
                if (messageContainer) messageContainer.innerHTML = '';
                
                // Add messages to container
                if (data.messages) {
                    data.messages.forEach(message => {
                        addMessageToContainer(message);
                    });
                }
                
                // Scroll to bottom
                scrollToBottom();
            })
            .catch(error => console.error('Error loading group messages:', error));
    }
    
    // Add a message to the container
    function addMessageToContainer(message) {
        if (!messageContainer) {
            console.error('Message container not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.is_mine ? 'message-sent' : 'message-received'}`;
        
        const senderSpan = document.createElement('div');
        senderSpan.className = 'message-sender';
        senderSpan.textContent = message.is_mine ? 'You' : message.sender;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = message.content;
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = message.timestamp;
        
        messageDiv.appendChild(senderSpan);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        messageContainer.appendChild(messageDiv);
    }
    
    // Send a message
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Sending message...');
            
            if (!messageInput || !messageInput.value.trim() || !currentChat.id) {
                console.log('No message to send or no chat selected');
                return;
            }
            
            const messageData = {
                content: messageInput.value.trim(),
                type: currentChat.type
            };
            
            // Add recipient or group ID based on chat type
            if (currentChat.type === 'direct') {
                messageData.recipient = currentChat.id;
            } else {
                messageData.group = currentChat.id;
            }
            
            console.log('Sending message data:', messageData);
            
            fetch('/messaging/send_message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(messageData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Message sent successfully:', data);
                // Add the sent message to the chat
                addMessageToContainer(data);
                
                // Clear input field
                messageInput.value = '';
                
                // Scroll to bottom
                scrollToBottom();
            })
            .catch(error => console.error('Error sending message:', error));
        });
    } else {
        console.error('Message form not found');
    }
    
    // Helper functions
    function scrollToBottom() {
        if (messageContainer) {
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Poll for new messages in active chat every 5 seconds
    setInterval(function() {
        if (currentChat.id) {
            if (currentChat.type === 'direct') {
                loadDirectMessages(currentChat.id);
            } else {
                loadGroupMessages(currentChat.id);
            }
        }
    }, 5000);
    
    // Handle group creation (only for teachers)
    if (document.getElementById('createGroupBtn')) {
        const createGroupBtn = document.getElementById('createGroupBtn');
        const saveGroupBtn = document.getElementById('saveGroupBtn');
        const createGroupForm = document.getElementById('createGroupForm');
        const groupNameInput = document.getElementById('groupName');
        
        // Show modal when button is clicked
        createGroupBtn.addEventListener('click', function() {
            console.log('Opening create group modal');
            $('#createGroupModal').modal('show');
        });
        
        // Create the group
        if (saveGroupBtn) {
            saveGroupBtn.addEventListener('click', function() {
                console.log('Saving group...');
                // Validate form
                if (!groupNameInput || !groupNameInput.value.trim()) {
                    console.log('No group name provided');
                    return;
                }
                
                // Get selected members
                const memberCheckboxes = document.querySelectorAll('.member-list input[type="checkbox"]:checked');
                const members = Array.from(memberCheckboxes).map(checkbox => checkbox.value);
                
                console.log('Creating group with members:', members);
                
                // Create group data
                const groupData = {
                    name: groupNameInput.value.trim(),
                    members: members
                };
                
                fetch('/messaging/create_group/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(groupData)
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Group created:', data);
                    // Add the new group to the list
                    const groupList = document.querySelector('.group-list');
                    
                    if (groupList) {
                        // Add new group item
                        const groupItem = document.createElement('a');
                        groupItem.className = 'list-group-item list-group-item-action group-item';
                        groupItem.setAttribute('href', '#');
                        groupItem.setAttribute('data-id', data.id);
                        
                        groupItem.innerHTML = `
                            <div class="d-flex w-100 justify-content-between align-items-center">
                                <div>
                                    <i class="fas fa-users mr-2"></i>
                                    <span>${data.name}</span>
                                </div>
                            </div>
                        `;
                        
                        groupList.appendChild(groupItem);
                    }
                    
                    // Reset form and close modal
                    if (createGroupForm) createGroupForm.reset();
                    $('#createGroupModal').modal('hide');
                })
                .catch(error => console.error('Error creating group:', error));
            });
        }
    }
}); 