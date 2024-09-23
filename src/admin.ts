import {Modal} from 'flowbite';
import type {ModalOptions, ModalInterface} from 'flowbite';

interface IAdmin {
  id: number;
  username: string;
  email: string;
  is_deleted: boolean;
}

const $modalElement: HTMLElement = document.querySelector('#editAdminModal');
const $addAdminModalElement: HTMLElement =
  document.querySelector('#add-admin-modal');

const modalOptions: ModalOptions = {
  placement: 'bottom-right',
  backdrop: 'dynamic',
  backdropClasses:
    'bg-gray-900 bg-opacity-50 dark:bg-opacity-80 fixed inset-0 z-40',
  // closable: true,
};

const modal: ModalInterface = new Modal($modalElement, modalOptions);
const addModal: ModalInterface = new Modal($addAdminModalElement, modalOptions);

const $buttonElements = document.querySelectorAll('.admin-edit-button');
$buttonElements.forEach(e =>
  e.addEventListener('click', () => {
    editAdmin(JSON.parse(e.getAttribute('data-target')));
  }),
);

// closing add user modal
const editModalCloseBtn = document.querySelector('#editAdminModalCloseButton');
if (editModalCloseBtn) {
  editModalCloseBtn.addEventListener('click', () => {
    modal.hide();
  });
}

// search flow
const searchInput: HTMLInputElement = document.querySelector(
  '#table-search-admins',
);
const searchInputButton = document.querySelector('#table-search-admin-button');
if (searchInputButton && searchInput) {
  searchInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchInput.value);
    window.location.href = `${url.href}`;
  });
}
const deleteButtons = document.querySelectorAll('.delete-admin-btn');

deleteButtons.forEach(e => {
  e.addEventListener('click', async () => {
    if (confirm('Are sure?')) {
      let id = e.getAttribute('data-admin-id');
      const response = await fetch(`/admin/delete/${id}`, {
        method: 'DELETE',
      });
      if (response.status == 200) {
        location.reload();
      }
    }
  });
});

// restore flow
const restoreButtons = document.querySelectorAll('.restore-admin-btn');
restoreButtons.forEach(e => {
  e.addEventListener('click', async () => {
    if (confirm('Are sure?')) {
      let id = e.getAttribute('data-admin-id');
      const response = await fetch(`/admin/restore/${id}`, {
        method: 'POST',
      });
      if (response.status == 200) {
        location.reload();
      }
    }
  });
});

function editAdmin(admin: IAdmin) {
  let input: HTMLInputElement = document.querySelector('#admin-edit-username');
  input.value = admin.username;
  input = document.querySelector('#admin-edit-id');
  input.value = admin.id.toString();
  input = document.querySelector('#admin-edit-email');
  input.value = admin.email;
  input = document.querySelector('#admin-edit-password');
  input.value = '*******';
  input = document.querySelector('#admin-edit-password_confirmation');
  input.value = '*******';
  input = document.querySelector('#admin-edit-next_url');
  input.value = window.location.href;
  modal.show();
}
